from pyldapi import Renderer
from vocprez.model.profiles import profile_nvs
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import DC, ORG
from vocprez import _config as config
import requests
from flask import Response, render_template


class MappingRenderer(Renderer):
    def __init__(self, request, int_ext, mapping_id):
        self.request = request
        self.profiles = {"nvs": profile_nvs}
        self.uri = "http://vocab.nerc.ac.uk/mapping/" + int_ext + "/" + mapping_id + "/"

        super().__init__(self.request, self.uri, self.profiles, "nvs")

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

    def _get_mapping_rdf(self):
        r = requests.get(
            config.SPARQL_ENDPOINT,
            params={"query": "DESCRIBE <{}>".format(self.uri)},
            auth=(config.SPARQL_USERNAME, config.SPARQL_PASSWORD)
        )

        g = Graph().parse(data=r.text, format="turtle")
        return g

    def _render_nvs_rdf(self):
        g = self._get_mapping_rdf()
        g.bind("dc", DC)
        REG = Namespace("http://purl.org/linked-data/registry#")
        g.bind("reg", REG)
        g.bind("org", ORG)

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
        g = self._get_mapping_rdf()

        mapping = {}
        for p, o in g.predicate_objects(subject=URIRef(self.uri)):
            if str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#subject":
                mapping["subject"] = str(o)
            elif str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate":
                mapping["predicate"] = str(o)
            elif str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#object":
                mapping["object"] = str(o)
            elif str(p) == "http://purl.org/dc/elements/1.1/modified":
                mapping["modified"] = str(o)
            elif str(p) == "http://purl.org/linked-data/registry#status":
                mapping["status"] = str(o)
            elif str(p) == "http://purl.org/linked-data/registry#submitter":
                for p2, o2 in g.predicate_objects(subject=o):
                    if str(p2) == "http://purl.org/linked-data/registry#title":
                        mapping["title"] = str(o2)
                    elif str(p2) == "http://purl.org/linked-data/registry#name":
                        mapping["name"] = str(o2)
                    elif str(p2) == "http://www.w3.org/ns/org#memberOf":
                        mapping["memberof"] = str(o2)


        _template_context = {
            "uri": self.uri,
            "subject": mapping["subject"],
            "predicate": mapping["predicate"],
            "object": mapping["object"],
            "modified": mapping["modified"],
            "status": mapping["status"],
            "submitter_title": mapping.get("title"),
            "submitter_name": mapping.get("name"),
            "submitter_memberof": mapping.get("memberof"),
        }

        return Response(
            render_template("mapping.html", **_template_context), headers=self.headers
        )
