from vocprez import __version__
from pyldapi import Renderer
from flask import Response, render_template
from rdflib import Graph, URIRef, Literal, XSD, RDF
from rdflib.namespace import DCTERMS, OWL, SKOS, Namespace, NamespaceManager
from vocprez.model.profiles import profile_dcat, profile_dd, profile_nvs, profile_skos
import json as j
from vocprez.model.vocabulary import Vocabulary, VocabularyRenderer
import logging
import requests
import vocprez._config as config
from vocprez.utils import serialize_by_mediatype


class NvsVocabularyRenderer(VocabularyRenderer):
    def __init__(self, request, vocab, language="en"):
        self.profiles = {
            "nvs": profile_nvs,
            "dcat": profile_dcat,
            "skos": profile_skos,
            "dd": profile_dd
        }
        self.vocab = vocab
        self.uri = self.vocab.uri
        self.language = language
        self.request = request

        # puv_vocabs_ids = [
        #     "A05",
        #     "P01",
        #     "S02",
        #     "S03",
        #     "S04",
        #     "S05",
        #     "S06",
        #     "S07",
        #     "S09",
        #     "S10",
        #     "S11",
        #     "S12",
        #     "S13",
        #     "S14",
        #     "S15",
        #     "S18",
        #     "S19",
        #     "S20",
        #     "S21",
        #     "S22",
        #     "S23",
        #     "S24",
        #     "S25",
        #     "S26",
        #     "S27",
        #     "S29",
        #     "S30"
        # ]
        # if any(f"/{x}/" in self.uri for x in puv_vocabs_ids):
        self.is_puv_vocab = False
        for op in vocab.other_properties:
            if op.uri == "http://purl.org/dc/terms/conformsTo" and op.value == URIRef("https://w3id.org/env/puv"):
                self.is_puv_vocab = True

        super(VocabularyRenderer, self).__init__(request, vocab.uri, self.profiles, "nvs")

    def render(self):
        # try returning alt profile
        response = super().render()
        if response is not None:
            return response
        elif self.profile == "dcat":
            if self.mediatype in Renderer.RDF_SERIALIZER_TYPES_MAP:
                return self._render_dcat_rdf()
            else:
                return self._render_dcat_html()
        elif self.profile == "skos":
            if self.mediatype in Renderer.RDF_SERIALIZER_TYPES_MAP:
                return self._render_skos_rdf()
            else:
                return self._render_dcat_html()  # same as DCAT, for now
        elif self.profile == "dd":
            return self._render_dd_json()
        elif self.profile == "nvs":
            if (
                    self.mediatype in Renderer.RDF_MEDIA_TYPES
                    or self.mediatype in Renderer.RDF_SERIALIZER_TYPES_MAP
            ):
                return self._render_nvs_rdf()
            else:
                return self._render_nvs_html()

    def _render_nvs_rdf(self):
        if "/standard_name" in self.request.base_url:
            q = f"""
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX pav: <http://purl.org/pav/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                
                CONSTRUCT {{
                  <{config.ABSOLUTE_URI_BASE}/standard_name/> ?p ?o . 
                  
                  <{config.ABSOLUTE_URI_BASE}/standard_name/> skos:member ?x .
                
                  ?x ?p2 ?o2 .                
                }}
                WHERE {{
                  {{
                    <{config.ABSOLUTE_URI_BASE}/collection/P07/current/> ?p ?o .
                  
                    MINUS {{ <{config.ABSOLUTE_URI_BASE}/collection/P07/current/> skos:member ?o . }}
                  }}
                  
                  {{
                    <{config.ABSOLUTE_URI_BASE}/collection/P07/current/> skos:member ?m .
                    ?m a skos:Concept .
                
                    ?m ?p2 ?o2 .
                
                    BIND (URI(CONCAT("{config.ABSOLUTE_URI_BASE}/standard_name/", STRAFTER(STR(?m),"/current/"))) AS ?x)
                  }}
                }}
                """
        elif "/scheme/" in self.request.base_url:
            q = """
                PREFIX dc: <http://purl.org/dc/terms/>
                PREFIX dce: <http://purl.org/dc/elements/1.1/>
                PREFIX grg: <http://www.isotc211.org/schemas/grg/>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX pav: <http://purl.org/pav/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX void: <http://rdfs.org/ns/void#>                
                
                CONSTRUCT {
                  <xxx> ?p ?o .
                  
                  ?m skos:inScheme <xxx> .
                
                  ?m ?p2 ?o2 .
                }
                WHERE {
                  <xxx> ?p ?o .
                
                  ?m skos:inScheme <xxx>.
                
                  ?m ?p2 ?o2 .
                }
                """.replace("xxx", self.vocab.uri)
        else:
            q = """
                PREFIX dc: <http://purl.org/dc/terms/>
                PREFIX dce: <http://purl.org/dc/elements/1.1/>
                PREFIX grg: <http://www.isotc211.org/schemas/grg/>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                PREFIX pav: <http://purl.org/pav/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX void: <http://rdfs.org/ns/void#>
                
                CONSTRUCT {
                  <xxx> ?p ?o . 
                  
                  <xxx> skos:member ?m .
                
                  ?m ?p2 ?o2 .              
                }
                WHERE {
                  {
                    <xxx> ?p ?o .
                  
                    MINUS { <xxx> skos:member ?o . }
                  }
                  
                  {
                    <xxx> skos:member ?m .
                    ?m a skos:Concept .
                
                    ?m ?p2 ?o2 .
                
                    FILTER ( ?p2 != skos:broaderTransitive )
                    FILTER ( ?p2 != skos:narrowerTransitive )
                  }
                }
                """.replace("xxx", self.vocab.uri)

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
        _template_context = {
            "version": __version__,
            "uri": self.uri,
            "vocab": self.vocab,
            "title": self.vocab.title,
            "is_puv_vocab": self.is_puv_vocab
        }

        return Response(
            render_template("vocabulary.html", **_template_context),
            headers=self.headers,
        )

    def _render_dd_json(self):
        concepts = {}
        concepts2 = []
        if self.vocab.concepts:
            for c in self.vocab.concepts:
                concepts[c[0]] = c[1]
            for k, v in concepts.items():
                concepts2.append({
                    "uri": k,
                    "prefLabel": v
                })
        return Response(j.dumps(concepts2), mimetype="application/json", headers=self.headers)

    def _render_skos_rdf(self):
        g = Graph()
        g.bind("skos", SKOS)
        s = URIRef(self.vocab.uri)
        if self.vocab.collections == "Collection":
            g.add((s, RDF.type, SKOS.Collection))
        else:
            g.add((s, RDF.type, SKOS.ConceptScheme))
        g.add((s, SKOS.prefLabel, Literal(self.vocab.title)))
        g.add((s, SKOS.definition, Literal(self.vocab.description)))
        # if self.vocab.hasTopConcept:
        #     for c in self.vocab.hasTopConcept:
        #         g.add((s, SKOS.hasTopConcept, URIRef(c[0])))
        #         g.add((URIRef(c[0]), SKOS.prefLabel, Literal(c[1])))
        if not self.vocab.concepts or len(self.vocab.concepts) == 0:
            from vocprez.source import NvsSPARQL
            concepts = NvsSPARQL(self.vocab.uri, self.request, language=self.request.values.get("lang")).list_concepts()
            for concept in concepts:
                g.add((s, SKOS.inScheme, URIRef(concept[0])))
                g.add((URIRef(concept[0]), SKOS.prefLabel, Literal(concept[1])))

        else:
            for c in self.vocab.concepts:
                if self.vocab.collections == "Collection":
                    g.add((s, SKOS.member, URIRef(c[0])))
                else:
                    g.add((s, SKOS.inScheme, URIRef(c[0])))
                g.add((URIRef(c[0]), SKOS.prefLabel, Literal(c[1])))

        # serialise in the appropriate RDF format
        if self.mediatype in ["application/rdf+json", "application/json"]:
            return Response(g.serialize(format="json-ld"), mimetype=self.mediatype, headers=self.headers)
        else:
            return Response(g.serialize(format=self.mediatype), mimetype=self.mediatype, headers=self.headers)
