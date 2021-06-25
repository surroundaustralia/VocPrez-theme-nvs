from vocprez import __version__
from pyldapi import Renderer
from flask import Response, render_template, g
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS
from vocprez.model.profiles import profile_skos, profile_nvs, profile_puv
import vocprez._config as config
from typing import List
from vocprez.model.property import Property
from vocprez.model.concept import Concept, ConceptRenderer
import requests
import logging
from vocprez.utils import serialize_by_mediatype, get_vocab_uri_from_concept_uri


class NvsConcept:
    def __init__(
        self,
        vocab_uri,
        uri,
        prefLabel,
        definition,
        related_instances,
        annotations=None,
        other_properties: List[Property] = None,
        puv_properties: List[Property] = None
    ):
        self.vocab_uri = vocab_uri
        self.uri = uri
        self.prefLabel = prefLabel
        self.definition = definition
        self.related_instances = related_instances
        self.annotations = annotations
        self.agents = None

        self.other_properties = other_properties
        self.puv_properties = puv_properties


class NvsConceptRenderer(ConceptRenderer):
    def __init__(self, request, concept):
        self.request = request
        self.profiles = {
            "nvs": profile_nvs,
            "skos": profile_skos,
        }
        self.concept = concept

        # Only make the PUV profile available for certain vocabs
        # TODO: replace with a lookup for vocab conformsTo PUV data
        puv_vocabs_ids = [
            "A05",
            "P01",
            "S02",
            "S03",
            "S04",
            "S05",
            "S06",
            "S07",
            "S09",
            "S10",
            "S11",
            "S12",
            "S13",
            "S14",
            "S15",
            "S18",
            "S19",
            "S20",
            "S21",
            "S22",
            "S23",
            "S24",
            "S25",
            "S26",
            "S27",
            "S29",
            "S30"
        ]
        if any(f"/{x}/" in self.concept.vocab_uri for x in puv_vocabs_ids):
            self.profiles["puv"] = profile_puv

        super(ConceptRenderer, self).__init__(self.request, self.concept.uri, self.profiles, "nvs")

    def render(self):
        # try returning alt profile
        response = super().render()
        if response is not None:
            return response
        elif self.profile == "nvs":
            if (
                self.mediatype in Renderer.RDF_MEDIA_TYPES
                or self.mediatype in Renderer.RDF_SERIALIZER_TYPES_MAP
            ):
                return self._render_nvs_rdf()
            else:
                return self._render_nvs_html()
        elif self.profile == "puv":
            if (
                self.mediatype in Renderer.RDF_MEDIA_TYPES
                or self.mediatype in Renderer.RDF_SERIALIZER_TYPES_MAP
            ):
                return self._render_puv_rdf()
            else:
                return self._render_puv_html()

    def _render_nvs_rdf(self):
        q = """
            PREFIX dc: <http://purl.org/dc/terms/>
            PREFIX dce: <http://purl.org/dc/elements/1.1/>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX pav: <http://purl.org/pav/>
            PREFIX prov: <https://www.w3.org/ns/prov#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX void: <http://rdfs.org/ns/void#>
            
            CONSTRUCT {
              <xxx> ?p ?o .
              
              # remove provenance, for now
              # ?s ?p2 ?o2 .              
              # ?s rdf:subject <xxx> ;
              #   prov:has_provenance ?m .              
            }
            WHERE {
                <xxx> ?p ?o .
              
                # remove provenance, for now
                # OPTIONAL {
                #     ?s rdf:subject <xxx> ;
                #        prov:has_provenance ?m .
                #         
                #     # { ?s ?p2 ?o2 }
                # }
                
                # exclude PUV properties from NVS view
                FILTER (!STRSTARTS(STR(?p), "https://w3id.org/env/puv#"))
            }        
            """.replace("xxx", self.concept.uri)
        r = requests.get(
            config.SPARQL_ENDPOINT,
            params={"query": q},
            headers={"Accept": self.mediatype}
        )

        return Response(
            r.text,
            mimetype=self.mediatype,
            headers=self.headers,
        )

    def _render_nvs_html(self):
        if "/standard_name/" in self.concept.vocab_uri:
            self.concept.vocab_uri = "http://vocab.nerc.ac.uk/standard_name/"
        _template_context = {
            "version": __version__,
            "vocab_uri": self.concept.vocab_uri,
            "vocab_title": g.VOCABS[self.concept.vocab_uri].title,
            "uri": self.request.values.get("uri"),
            "concept": self.concept,
        }

        return Response(
            render_template("concept.html", **_template_context), headers=self.headers
        )

    def _render_skos_rdf(self):
        g = Graph()
        g.bind("dct", DCTERMS)
        g.bind("skos", SKOS)

        c = URIRef(self.concept.uri)

        # Concept SKOS metadata
        g.add((
            c,
            RDF.type,
            SKOS.Concept
        ))
        g.add((
            c,
            SKOS.prefLabel,
            Literal(self.concept.prefLabel, lang=config.DEFAULT_LANGUAGE)
        ))
        g.add((
            c,
            SKOS.definition,
            Literal(self.concept.definition, lang=config.DEFAULT_LANGUAGE)
        ))

        for k, v in self.concept.related_instances.items():
            for k2, v2 in v.items():
                if k2 == "instances":
                    for inst in v2:
                        g.add((
                            c,
                            URIRef(k),
                            URIRef(inst[0])  # only URIs for RDF, not prefLabels too
                        ))

        if self.concept.other_properties is not None:
            for prop in self.concept.other_properties:
                # SKOS & DCTERMS properties only
                if str(prop.uri).startswith("http://www.w3.org/2004/02/skos/core#") or \
                   str(prop.uri).startswith("http://purl.org/dc/terms/"):
                    if str(prop.value).startswith("http"):
                        g.add((c, URIRef(prop.uri), URIRef(prop.value)))
                    else:
                        g.add((c, URIRef(prop.uri), Literal(prop.value)))

        # serialise in the appropriate RDF format
        if self.mediatype in ["application/rdf+json", "application/json"]:
            graph_text = g.serialize(format="json-ld")
        else:
            graph_text = g.serialize(format=self.mediatype)

        return Response(
            graph_text,
            mimetype=self.mediatype,
            headers=self.headers,
        )

    def _render_puv_html(self):
        _template_context = {
            "version": __version__,
            "vocab_uri": self.concept.vocab_uri if self.concept.vocab_uri is not None else self.request.values.get("vocab_uri"),
            "vocab_title": g.VOCABS[self.concept.vocab_uri].title,
            "uri": self.request.values.get("uri"),
            "concept": self.concept,
        }

        return Response(
            render_template("concept_puv.html", **_template_context), headers=self.headers
        )

    def _render_puv_rdf(self):
        q = """
            PREFIX dc: <http://purl.org/dc/terms/>
            PREFIX dce: <http://purl.org/dc/elements/1.1/>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX pav: <http://purl.org/pav/>
            PREFIX prov: <https://www.w3.org/ns/prov#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX void: <http://rdfs.org/ns/void#>

            CONSTRUCT {
              <xxx> ?p ?o .
              # ?s ?p2 ?o2 .

              # ?s rdf:subject <xxx> ;
              #   prov:has_provenance ?m .              
            }
            WHERE {
                <xxx> ?p ?o .

                # exclude PUV properties from NVS view
                FILTER (!STRSTARTS(STR(?p), "https://w3id.org/env/puv#"))
            }        
            """.replace("xxx", self.concept.uri)
        r = requests.get(
            config.SPARQL_ENDPOINT,
            params={"query": q},
            headers={"Accept": "text/turtle"}
        )

        g = Graph().parse(data=r.text, format="turtle")

        g.parse(
            data="""
            @prefix puv: <https://w3id.org/env/puv#> .

            <xxx> 
                a puv:Parameter ;
                puv:biologicalObject <http://vocab.nerc.ac.uk/collection/S25/current/BE006569/> ;
                puv:chemicalObject <http://vocab.nerc.ac.uk/collection/S27/current/CS003687/> ;
                puv:matrix <http://vocab.nerc.ac.uk/collection/S26/current/MAT01963/> ;
                puv:matrixRelationship <http://vocab.nerc.ac.uk/collection/S02/current/S041/> ;
                puv:property <http://vocab.nerc.ac.uk/collection/S06/current/S0600045/> ;
                puv:uom <http://vocab.nerc.ac.uk/collection/P06/current/UUKG/> ;
            .
            """.replace("xxx", self.concept.uri),
            format="turtle"
        )

        return Response(
            serialize_by_mediatype(g, self.mediatype),
            mimetype=self.mediatype,
            headers=self.headers,
        )
