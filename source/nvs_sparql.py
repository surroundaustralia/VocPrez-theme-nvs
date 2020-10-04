import logging
import dateutil.parser
from flask import g
import vocprez.source.utils
from vocprez import _config as config
from vocprez.model.vocabulary import Vocabulary
from ..model.property import Property
from ._source import Source
from .utils import sparql_query
from rdflib import Literal, URIRef


class NvsSPARQL(Source):
    """Source for a generic SPARQL endpoint
    """

    def __init__(self, vocab_uri, request, language=None):
        super().__init__(vocab_uri, request, language)

    @staticmethod
    def collect(details):
        """
        For this source, one SPARQL endpoint is given for a series of vocabs which are all separate ConceptSchemes

        'ga-jena-fuseki': {
            'source': VocabSource.SPARQL,
            'sparql_endpoint': 'http://dev2.nextgen.vocabs.ga.gov.au/fuseki/vocabs',
            'sparql_username': '<sparql_user>', # Optional username for SPARQL endpoint
            'sparql_password': '<sparql_password>', # Optional password for SPARQL endpoint
            #'uri_filter_regex': '.*', # Regular expression to filter vocabulary URIs - Everything
            #'uri_filter_regex': '^http(s?)://pid.geoscience.gov.au/def/voc/ga/', # Regular expression to filter vocabulary URIs - GA
            #'uri_filter_regex': '^https://gcmdservices.gsfc.nasa.gov', # Regular expression to filter vocabulary URIs - GCMD
            'uri_filter_regex': '^http(s?)://resource.geosciml.org/', # Regular expression to filter vocabulary URIs - CGI

        },
        """
        logging.debug("SPARQL collect()...")

        # Get all the ConceptSchemes from the SPARQL endpoint
        # Interpret each CS as a Vocab
        q = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT * WHERE {{
                {{?cs a skos:ConceptScheme .}}
                UNION
                {{?cs a skos:Collection .}}
                ?cs a ?t .
                OPTIONAL {{ ?cs skos:prefLabel ?title .
                    FILTER(lang(?title) = "{language}" || lang(?title) = "") }}
                OPTIONAL {{ ?cs dcterms:created ?created }}
                OPTIONAL {{ ?cs dcterms:issued ?issued }}
                OPTIONAL {{ ?cs dcterms:date ?modified }}
                OPTIONAL {{ ?cs dcterms:creator ?creator }}
                OPTIONAL {{ ?cs dcterms:publisher ?publisher }}
                OPTIONAL {{ ?cs owl:versionInfo ?version }}
                OPTIONAL {{ ?cs dcterms:description ?description .
                    FILTER(lang(?description) = "{language}" || lang(?description) = "") }}   
                # NVS special properties                 
                OPTIONAL {{
                    ?cs <http://www.isotc211.org/schemas/grg/RE_RegisterManager> ?registermanager .
                    ?cs <http://www.isotc211.org/schemas/grg/RE_RegisterOwner> ?registerowner .
                }}                
                OPTIONAL {{ ?cs rdfs:seeAlso ?seeAlso }}                
            }} 
            ORDER BY ?title
            """.format(language=config.DEFAULT_LANGUAGE)
        # record just the IDs & title for the VocPrez in-memory vocabs list
        concept_schemes = vocprez.source.utils.sparql_query(
            q,
            details["sparql_endpoint"],  # must specify a SPARQL endpoint if this source is to be a SPARQL source
            details.get("sparql_username"),
            details.get("sparql_password"),
        )
        assert concept_schemes is not None, "Unable to query for ConceptSchemes"

        sparql_vocabs = {}
        for cs in concept_schemes:
            vocab_id = cs["cs"]["value"]

            other_properties = []
            other_properties.append(
                Property(
                    "http://purl.org/dc/terms/identifier",
                    "Identifier",
                    Literal(
                        cs["cs"]["value"]
                            .replace("http://vocab.nerc.ac.uk/collection/", "")
                            .replace("http://vocab.nerc.ac.uk/scheme/", "")
                            .replace("/current/", "")
                    )
                )
            )
            if cs.get("registermanager") is not None:
                other_properties.append(
                    Property(
                        "http://www.isotc211.org/schemas/grg/RE_RegisterManager",
                        "Register Manager",
                        Literal(cs["registermanager"]["value"])
                    )
                )
            if cs.get("registerowner") is not None:
                other_properties.append(
                    Property(
                        "http://www.isotc211.org/schemas/grg/RE_RegisterOwner",
                        "Register Owner",
                        Literal(cs["registerowner"]["value"])
                    )
                )
            if cs.get("seeAlso") is not None:
                other_properties.append(
                    Property(
                        "http://www.w3.org/2000/01/rdf-schema#seeAlso",
                        "See Also",
                        URIRef(cs["seeAlso"]["value"])
                    )
                )

            sparql_vocabs[vocab_id] = Vocabulary(
                cs["cs"]["value"],
                cs["cs"]["value"],
                cs["title"].get("value") or vocab_id if cs.get("title") else vocab_id,  # Need str for sorting, not None
                cs["description"].get("value") if cs.get("description") is not None else None,
                cs["creator"].get("value") if cs.get("creator") is not None else None,
                dateutil.parser.parse(cs.get("created").get("value")) if cs.get("created") is not None else None,
                # dct:issued not in Vocabulary
                # dateutil.parser.parse(cs.get('issued').get('value')) if cs.get('issued') is not None else None,
                dateutil.parser.parse(cs.get("modified").get("value")) if cs.get("modified") is not None else None,
                cs["version"].get("value") if cs.get("version") is not None else None,  # versionInfo
                config.VocabSource.NvsSPARQL,  # TODO: replace this var with a reference to self class type (Source type)
                collections=str(cs["t"]["value"]).split("#")[-1],
                sparql_endpoint=details["sparql_endpoint"],
                sparql_username=details.get("sparql_username"),
                sparql_password=details.get("sparql_password"),
                other_properties=other_properties
            )
        g.VOCABS = {**g.VOCABS, **sparql_vocabs}
        logging.debug("SPARQL collect() complete.")

    def list_concepts_for_a_collection(self):
        vocab = g.VOCABS[self.vocab_uri]
        q = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT DISTINCT ?c ?pl
            WHERE {{
                    <{uri}> skos:member ?c .

                    ?c skos:prefLabel ?pl .
                    FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
            }}
            ORDER BY ?pl
            """.format(uri=vocab.uri, language=self.language)

        return [
            (concept["c"]["value"], concept["pl"]["value"])
            for concept in sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)
        ]

    def get_vocabulary(self):
        """
        Get a vocab from the cache
        :return:
        :rtype:
        """
        # is this a Concept Scheme or a Collection?
        if g.VOCABS[self.vocab_uri].collections == "ConceptScheme":
            g.VOCABS[self.vocab_uri].concept_hierarchy = self.get_concept_hierarchy()
            g.VOCABS[self.vocab_uri].concepts = self.list_concepts()
            g.VOCABS[self.vocab_uri].collections = self.list_collections()
        else:  # vocab.collection == "Collection":
            g.VOCABS[self.vocab_uri].concepts = self.list_concepts_for_a_collection()

        return g.VOCABS[self.vocab_uri]
