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
        api_concept_uri = "$DB2RDF_COLLECTIONS_URI" + self.concept.uri.split("/collection/")[1]
        logging.info("api_concept_uri")
        logging.info(api_concept_uri)
        r = requests.get(api_concept_uri)

        if self.mediatype in ["application/rdf+xml", "application/xml", "text/xml"]:
            return Response(
                r.text,
                mimetype=self.mediatype,
                headers=self.headers,
            )
        else:
            g = Graph().parse(data=r.text, format="xml")

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
