from vocprez import __version__
from pyldapi import Renderer
from flask import Response, render_template, g
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS
from vocprez.model.profiles import profile_skos, profile_nvs
import vocprez._config as config
from typing import List
from vocprez.model.property import Property
from vocprez.model.concept import Concept, ConceptRenderer
import requests
import logging


class NvsConceptRenderer(ConceptRenderer):
    def __init__(self, request, concept):
        self.request = request
        self.profiles = {
            "nvs": profile_nvs,
            "skos": profile_skos
        }
        self.concept = concept

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

    def _render_nvs_rdf(self):
        r = requests.get(
            config.SPARQL_ENDPOINT,
            params={"query": "DESCRIBE <{}>".format(self.concept.uri)},
            headers={"Accept": "text/turtle"}
        )

        g = Graph().parse(data=r.text, format="turtle")

        prefixes = {
            "dc": "http://purl.org/dc/terms/",
            "dce": "http://purl.org/dc/elements/1.1/",
            "grg": "http://www.isotc211.org/schemas/grg/",
            "owl": "http://www.w3.org/2002/07/owl#",
            "pav": "http://purl.org/pav/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "void": "http://rdfs.org/ns/void#",
        }
        for k, v in prefixes.items():
            g.bind(k, v)

        # serialise in other RDF format
        if self.mediatype in ["application/rdf+json", "application/json"]:
            graph_text = g.serialize(format="json-ld")
        else:
            graph_text = g.serialize(format=self.mediatype)

        return Response(
            graph_text,
            mimetype=self.mediatype,
            headers=self.headers,
        )

    def _render_nvs_html(self):
        _template_context = {
            "version": __version__,
            "vocab_uri": self.concept.vocab_uri if self.concept.vocab_uri is not None else self.request.values.get("vocab_uri"),
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