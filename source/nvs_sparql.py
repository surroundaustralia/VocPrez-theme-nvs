import logging
import dateutil.parser
from flask import g
from vocprez import _config as config
from vocprez.model.vocabulary import Vocabulary
from vocprez.model.property import Property
from vocprez.source._source import *
import vocprez.utils as u
from rdflib import Literal, URIRef, Graph


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
                OPTIONAL {{ ?cs dcterms:modified ?modified }}
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
        concept_schemes = u.sparql_query(
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
        logging.debug("pickle latest standard_name")
        import requests
        from pathlib import Path
        import pickle

        r = requests.get("http://vocab.nerc.ac.uk/standard_name/")
        gr = Graph()
        gr.parse(data=r.text, format="xml")
        with open(Path(config.APP_DIR) / "cache" / "standard_name.p", "wb") as f:
            pickle.dump(gr, f)

        for cs in gr.query(q):
            vocab_id = str(cs["cs"])

            other_properties = []
            other_properties.append(
                Property(
                    "http://purl.org/dc/terms/identifier",
                    "Identifier",
                    Literal("standard_name")
                )
            )
            # the following properties are filled with blanks, not None, in the vocab
            # if cs.get("registermanager") is not None:
            #     other_properties.append(
            #         Property(
            #             "http://www.isotc211.org/schemas/grg/RE_RegisterManager",
            #             "Register Manager",
            #             Literal(cs["registermanager"])
            #         )
            #     )
            # if cs.get("registerowner") is not None:
            #     other_properties.append(
            #         Property(
            #             "http://www.isotc211.org/schemas/grg/RE_RegisterOwner",
            #             "Register Owner",
            #             Literal(cs["registerowner"])
            #         )
            #     )
            # if cs.get("seeAlso") is not None:
            #     other_properties.append(
            #         Property(
            #             "http://www.w3.org/2000/01/rdf-schema#seeAlso",
            #             "See Also",
            #             URIRef(cs["seeAlso"])
            #         )
            #     )

            sparql_vocabs[vocab_id] = Vocabulary(
                "standard_name",
                vocab_id,
                str(cs["title"]),
                str(cs["description"]),
                str(cs["creator"]),
                None,
                # dct:issued not in Vocabulary
                # dateutil.parser.parse(cs.get('issued').get('value')) if cs.get('issued') is not None else None,
                dateutil.parser.parse(cs.get("modified")),
                str(cs["version"]),  # versionInfo
                config.VocabSource.NvsSPARQL,
                collections="Collection",  # just like the other Collections
                sparql_endpoint=details["sparql_endpoint"],
                sparql_username=details.get("sparql_username"),
                sparql_password=details.get("sparql_password"),
                other_properties=other_properties
            )

        g.VOCABS = {}
        g.VOCABS.update(**sparql_vocabs)
        logging.debug("NvsSPARQL collect() complete.")

    # def get_concept_hierarchy(self):
    #     """
    #     Function to draw concept hierarchy for vocabulary
    #     """
    #
    #     def build_hierarchy(bindings_list, broader_concept=None, level=0):
    #         """
    #         Recursive helper function to build hierarchy list from a bindings list
    #         Returns list of tuples: (<level>, <concept>, <concept_preflabel>, <broader_concept>)
    #         """
    #         level += 1  # Start with level 1 for top concepts
    #         hier = []
    #
    #         narrower_list = sorted(
    #             [
    #                 binding_dict
    #                 for binding_dict in bindings_list
    #                 if (  # Top concept
    #                            (broader_concept is None)
    #                            and (binding_dict.get("broader_concept") is None)
    #                    )
    #                    or  # Narrower concept
    #                    (
    #                            (binding_dict.get("broader_concept") is not None)
    #                            and (
    #                                    binding_dict["broader_concept"]["value"] == broader_concept
    #                            )
    #                    )
    #             ],
    #             key=lambda binding_dict: binding_dict["concept_preflabel"]["value"],
    #         )
    #         for binding_dict in narrower_list:
    #             concept = binding_dict["concept"]["value"]
    #             hier += [
    #                         (
    #                             level,
    #                             concept,
    #                             binding_dict["concept_preflabel"]["value"],
    #                             binding_dict["broader_concept"]["value"]
    #                             if binding_dict.get("broader_concept")
    #                             else None,
    #                         )
    #                     ] + build_hierarchy(bindings_list, concept, level)
    #         return hier
    #
    #     vocab = g.VOCABS[self.vocab_uri]
    #
    #     query = """
    #         PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    #         PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    #
    #         SELECT distinct ?concept ?concept_preflabel ?broader_concept
    #         WHERE {{
    #             {{ ?concept skos:inScheme <{vocab_uri}> . }}
    #             UNION
    #             {{ ?concept skos:topConceptOf <{vocab_uri}> . }}
    #             UNION
    #             {{ <{vocab_uri}> skos:hasTopConcept ?concept . }}
    #             ?concept skos:prefLabel ?concept_preflabel .
    #             OPTIONAL {{
    #                 ?concept skos:broader ?broader_concept .
    #                 ?broader_concept skos:inScheme <{vocab_uri}> .
    #             }}
    #             FILTER(lang(?concept_preflabel) = "{language}" || lang(?concept_preflabel) = "")
    #         }}
    #         ORDER BY ?concept_preflabel
    #         """.format(
    #         vocab_uri=vocab.uri,
    #         language=self.language
    #     )
    #
    #     bindings_list = u.sparql_query(query, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)
    #
    #     assert bindings_list is not None, "SPARQL concept hierarchy query failed"
    #
    #     hierarchy = build_hierarchy(bindings_list)
    #
    #     return u.draw_concept_hierarchy(hierarchy, self.request, self.vocab_uri)

    def list_concepts(self, acc_dep=None):
        vocab = g.VOCABS[self.vocab_uri]

        if acc_dep == "accepted":
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT DISTINCT ?c ?pl ?broader ?dep
                WHERE {{
                    {{?c skos:inScheme <{vocab_uri}>}}

                    ?c a skos:Concept ;
                         skos:prefLabel ?pl .
                        
                    ?c <http://www.w3.org/2002/07/owl#deprecated> "false" .

                    OPTIONAL {{
                        {{?c skos:broader ?broader}}
                        UNION 
                        {{?broader skos:narrower ?c}}
                    }}

                    FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)
        elif acc_dep == "deprecated":
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT DISTINCT ?c ?pl ?broader ?dep
                WHERE {{
                    {{?c skos:inScheme <{vocab_uri}>}}

                    ?c a skos:Concept ;
                         skos:prefLabel ?pl .
                         
                    ?c <http://www.w3.org/2002/07/owl#deprecated> "true" .

                    OPTIONAL {{
                        {{?c skos:broader ?broader}}
                        UNION 
                        {{?broader skos:narrower ?c}}
                    }}

                    FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)
        else:
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT DISTINCT ?c ?pl ?broader ?dep
                WHERE {{
                    {{?c skos:inScheme <{vocab_uri}>}}

                    ?c a skos:Concept ;
                         skos:prefLabel ?pl .

                    OPTIONAL {{
                        {{?c skos:broader ?broader}}
                        UNION 
                        {{?broader skos:narrower ?c}}
                    }}

                    FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)

        return [
            (
                concept["c"]["value"],
                concept["pl"]["value"],
                concept["broader"]["value"] if concept.get("broader") else None
            )
            for concept in u.sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)
        ]

    def list_concepts_for_a_collection(self, acc_dep=None):
        vocab = g.VOCABS[self.vocab_uri]

        if acc_dep == "accepted":
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?c ?pl ?dep
                WHERE {{
                        <{vocab_uri}> skos:member ?c .
                        
                        ?c <http://www.w3.org/2002/07/owl#deprecated> "false" .

                        OPTIONAL {{
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }}

                        ?c skos:prefLabel ?pl .
                        FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)
        elif acc_dep == "deprecated":
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?c ?pl ?dep
                WHERE {{
                        <{vocab_uri}> skos:member ?c .
                        
                        ?c <http://www.w3.org/2002/07/owl#deprecated> "true" .

                        OPTIONAL {{
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }}

                        ?c skos:prefLabel ?pl .
                        FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)
        else:
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?c ?pl ?dep
                WHERE {{
                        <{vocab_uri}> skos:member ?c .

                        OPTIONAL {{
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }}

                        ?c skos:prefLabel ?pl .
                        FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)

        return [
            (
                concept["c"]["value"],
                concept["pl"]["value"],
                True if concept.get("dep") and concept["dep"]["value"] == "true" else False
            )
            for concept in u.sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)
        ]

    def list_concepts_for_standard_name(self, acc_dep=None):
        if acc_dep == "deprecated":
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?c ?pl ?dep
                WHERE {
                        <http://vocab.nerc.ac.uk/standard_name/> skos:member ?c .
                        
                        ?c <http://www.w3.org/2002/07/owl#deprecated> "true" .

                        OPTIONAL {
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }

                        ?c skos:prefLabel ?pl .
                }
                ORDER BY ?pl
                """
        else:
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    
                SELECT DISTINCT ?c ?pl ?dep
                WHERE {
                        <http://vocab.nerc.ac.uk/standard_name/> skos:member ?c .
    
                        OPTIONAL {
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }
    
                        ?c skos:prefLabel ?pl .
                }
                ORDER BY ?pl
                """

        import pickle
        from pathlib import Path
        return [
            (
                str(concept["c"]),
                str(concept["pl"]),
                True if concept.get("dep") and concept["dep"] == "true" else False
            )
            for concept in pickle.load(open(Path(config.APP_DIR) / "cache" / "standard_name.p", "rb")).query(q)
        ]

    def get_vocabulary(self, acc_dep=None):
        """
        Get a vocab from the cache
        :return:
        :rtype:
        """
        if self.vocab_uri == "http://vocab.nerc.ac.uk/standard_name/":
            g.VOCABS[self.vocab_uri].concepts = self.list_concepts_for_standard_name(acc_dep=acc_dep)
        # is this a Concept Scheme or a Collection?
        elif g.VOCABS[self.vocab_uri].collections == "ConceptScheme":
            g.VOCABS[self.vocab_uri].concept_hierarchy = self.get_concept_hierarchy()
            g.VOCABS[self.vocab_uri].collections = self.list_collections()
        else:  # vocab.collection == "Collection":
            g.VOCABS[self.vocab_uri].concepts = self.list_concepts_for_a_collection(acc_dep=acc_dep)

        return g.VOCABS[self.vocab_uri]

    def get_concept(self, uri):
        vocab = g.VOCABS[self.vocab_uri]
        q = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT DISTINCT *            
            WHERE {{
                <{concept_uri}> a skos:Concept ;
                                ?p ?o .

                OPTIONAL {{
                    ?o skos:prefLabel ?ropl .
                }}                
            }}
            """.format(
            concept_uri=uri
        )

        pl = None
        d = None
        s = {
            "provenance": None,
            "source": None,
            "wasDerivedFrom": None,
        }
        annotation_types = {
            "http://www.opengis.net/def/metamodel/ogc-na/status": "Status",
            # 'http://www.w3.org/2004/02/skos/core#altLabel': "Alternative Label",
            'http://www.w3.org/2004/02/skos/core#note': "Note",
            'http://www.w3.org/2004/02/skos/core#scopeNote': "Scope Note",
            'http://www.w3.org/2004/02/skos/core#hostryNote': "History Note",
        }
        annotations = []
        agent_types = {
            'http://purl.org/dc/terms/contributor': "Contributor",
            'http://purl.org/dc/terms/creator': "Creator",
            'http://purl.org/dc/terms/publisher': "Publisher",
        }
        agent = {}
        related_instance_types = {
            'http://www.w3.org/2004/02/skos/core#exactMatch': "Exact Match",
            'http://www.w3.org/2004/02/skos/core#closeMatch': "Close Match",
            'http://www.w3.org/2004/02/skos/core#broadMatch': "Broad Match",
            'http://www.w3.org/2004/02/skos/core#narrowMatch': "Narrow Match",
            'http://www.w3.org/2004/02/skos/core#broader': "Broader",
            'http://www.w3.org/2004/02/skos/core#narrower': "Narrower",
            'http://www.w3.org/2002/07/owl#sameAs': "Same As"
        }
        provenance_property_types = {
            "http://purl.org/pav/hasCurrentVersion": "Has Current Version",
            "http://purl.org/pav/version": "Version",
            "http://www.w3.org/2002/07/owl#deprecated": "Deprecated",
            "http://purl.org/pav/previousVersion": "Previous Version",
            "http://purl.org/dc/terms/isVersionOf": "Is Version Of",
            "http://purl.org/pav/authoredOn": "Authored On"
        }
        related_instances = {}

        other_properties = []
        unique_alt_labels = []
        for r in u.sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password):
            if r["p"]["value"] == "http://www.w3.org/2004/02/skos/core#prefLabel":
                pl = r["o"]["value"]
            elif r["p"]["value"] == "http://www.w3.org/2004/02/skos/core#definition":
                d = r["o"]["value"]
            elif r["p"]["value"] == "http://purl.org/dc/terms/provenance":
                s["provenance"] = r["o"]["value"]
            elif r["p"]["value"] == "http://purl.org/dc/terms/source":
                s["source"] = r["o"]["value"]
            elif r["p"]["value"] == "http://www.w3.org/ns/prov#wasDerivedFrom":
                s["wasDerivedFrom"] = r["o"]["value"]
            elif r["p"]["value"] in annotation_types.keys():
                annotations.append(Property(r["p"]["value"], annotation_types[r["p"]["value"]], r["o"]["value"]))
            elif r["p"]["value"] in related_instance_types.keys():
                if related_instances.get(r["p"]["value"]) is None:
                    related_instances[r["p"]["value"]] = {}
                    related_instances[r["p"]["value"]] = {
                        "instances": [],
                        "label": related_instance_types[r["p"]["value"]]
                    }
                related_instances[r["p"]["value"]]["instances"].append(
                    (r["o"]["value"], r["ropl"]["value"] if r.get("ropl") is not None else None)
                )
            elif r["p"]["value"] in provenance_property_types.keys():
                other_properties.append(
                    Property(r["p"]["value"], provenance_property_types[r["p"]["value"]], r["o"]["value"].rstrip(".0")))
            elif r["p"]["value"] == "http://www.w3.org/2004/02/skos/core#altLabel":
                if r["o"]["value"] not in unique_alt_labels:
                    unique_alt_labels.append(r["o"]["value"])
                    other_properties.append(
                        Property(r["p"]["value"], "Alternative Label", r["o"]["value"]))

            # TODO: Agents

            # TODO: more Annotations

        if pl is None:
            return None

        from vocprez.model.concept import Concept

        return Concept(
            self.vocab_uri,
            uri,
            pl,
            d,
            related_instances,
            annotations=annotations,
            other_properties=other_properties
        )

    def get_concept_hierarchy(self):
        """
        Function to draw concept hierarchy for vocabulary
        """

        def build_hierarchy(bindings_list, broader_concept=None, level=0):
            """
            Recursive helper function to build hierarchy list from a bindings list
            Returns list of tuples: (<level>, <concept>, <concept_preflabel>, <broader_concept>)
            """
            level += 1  # Start with level 1 for top concepts
            hier = []

            narrower_list = sorted(
                [
                    binding_dict
                    for binding_dict in bindings_list
                    if (  # Top concept
                               (broader_concept is None)
                               and (binding_dict.get("broader_concept") is None)
                       )
                       or  # Narrower concept
                       (
                               (binding_dict.get("broader_concept") is not None)
                               and (
                                       binding_dict["broader_concept"]["value"] == broader_concept
                               )
                       )
                ],
                key=lambda binding_dict: binding_dict["concept_preflabel"]["value"],
            )
            for binding_dict in narrower_list:
                concept = binding_dict["concept"]["value"]
                hier += [
                            (
                                level,
                                concept,
                                binding_dict["concept_preflabel"]["value"],
                                binding_dict["broader_concept"]["value"]
                                if binding_dict.get("broader_concept")
                                else None,
                            )
                        ] + build_hierarchy(bindings_list, concept, level)
            return hier

        vocab = g.VOCABS[self.vocab_uri]

        query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT distinct ?concept ?concept_preflabel ?broader_concept
            WHERE {{
                {{ ?concept skos:inScheme <{vocab_uri}> . }}
                UNION
                {{ ?concept skos:topConceptOf <{vocab_uri}> . }}
                UNION
                {{ <{vocab_uri}> skos:hasTopConcept ?concept . }}  
                ?concept skos:prefLabel ?concept_preflabel .
                OPTIONAL {{ 
                    ?concept skos:broader ?broader_concept .
                    {{ ?broader_concept skos:inScheme <{vocab_uri}> . }}
                    UNION
                    {{ ?broader_concept skos:topConceptOf <{vocab_uri}> . }}
                    UNION
                    {{ <{vocab_uri}> skos:hasTopConcept ?broader_concept . }}  
                }}
                FILTER(lang(?concept_preflabel) = "{language}" || lang(?concept_preflabel) = "")
            }}
            ORDER BY ?concept_preflabel
            """.format(
            vocab_uri=vocab.uri,
            language=self.language
        )
        try:
            bindings_list = u.sparql_query(query, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)

            assert bindings_list is not None, "SPARQL concept hierarchy query failed"

            hierarchy = build_hierarchy(bindings_list)

            return u.draw_concept_hierarchy(hierarchy, self.request, self.vocab_uri)
        except RecursionError as e:
            logging.warning("Encountered a recursion limit error for {}".format(self.vocab_uri))
            # make a flat list of concepts
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT DISTINCT ?c ?pl
                WHERE {{
                    ?c skos:inScheme <{vocab_uri}> .              

                    ?c skos:prefLabel ?pl .

                    FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)

            concepts = [
                (
                    concept["c"]["value"],
                    concept["pl"]["value"]
                )
                for concept in u.sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)
            ]

            concepts_html = "<br />".join(["<a href=\"{}\">{}</a>".format(c[0], c[1]) for c in concepts])
            return """<p><strong><em>This concept hierarchy cannot be displayed</em></strong><p>
                        <p>The flat list of all this Scheme's Concepts is:</p>
                        <p>{}</p>
                    """.format(concepts_html)
