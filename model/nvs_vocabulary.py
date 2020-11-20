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
        if self.vocab.collections == "Collection":
            if "/standard_name/" in self.vocab.uri:
                api_vocab_uri = "$DB2RDF_STANDARD_NAME_URI"
            else:
                api_vocab_uri = "$DB2RDF_COLLECTIONS_URI" + self.vocab.uri.split("/collection/")[1]
        else:
            api_vocab_uri = "$DB2RDF_SCHEMES_URI" + self.vocab.uri.split("/scheme/")[1]

        r = requests.get(api_vocab_uri)

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
            "uri": self.uri,
            "vocab": self.vocab,
            "title": self.vocab.title,
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
        if self.vocab.concepts:
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
