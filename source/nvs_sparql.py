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
        logging.debug("NvsSPARQL collect()...")

        # Get all the ConceptSchemes from the SPARQL endpoint
        # Interpret each CS as a Vocab
        q = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT * 
            WHERE {
                VALUES ?t { skos:ConceptScheme skos:Collection }
                ?v a ?t .
                OPTIONAL { ?v skos:prefLabel ?title .
                           FILTER(lang(?title) = "en" || lang(?title) = "") 
                }
                OPTIONAL { ?v dcterms:created ?created }
                OPTIONAL { ?v dcterms:issued ?issued }
                OPTIONAL { ?v dcterms:date ?modified }
                OPTIONAL { ?v dcterms:modified ?modified }
                OPTIONAL { ?v dcterms:creator ?creator }
                OPTIONAL { ?v dcterms:publisher ?publisher }
                OPTIONAL { ?v owl:versionInfo ?version }
                OPTIONAL { ?v dcterms:description ?description .
                           FILTER(lang(?description) = "en" || lang(?description) = "") 
                }
                # NVS special properties                 
                OPTIONAL {
                    ?v <http://www.isotc211.org/schemas/grg/RE_RegisterManager> ?registermanager .
                    ?v <http://www.isotc211.org/schemas/grg/RE_RegisterOwner> ?registerowner .
                }            
                OPTIONAL { ?v rdfs:seeAlso ?seeAlso }
            }
            ORDER BY ?title
            """
        # record just the IDs & title for the VocPrez in-memory vocabs list
        vocabularies = u.sparql_query(
            q,
            details["sparql_endpoint"],  # must specify a SPARQL endpoint if this source is to be a SPARQL source
            details.get("sparql_username"),
            details.get("sparql_password"),
        )
        assert vocabularies is not None, "Unable to query for Vocabularies"

        sparql_vocabs = {}
        for v in vocabularies:
            vocab_uri = v["v"]["value"]

            other_properties = []
            other_properties.append(
                Property(
                    "http://purl.org/dc/terms/identifier",
                    "Identifier",
                    Literal(u.get_vocab_id(v["v"]["value"]))
                )
            )
            if v.get("registermanager") is not None:
                other_properties.append(
                    Property(
                        "http://www.isotc211.org/schemas/grg/RE_RegisterManager",
                        "Register Manager",
                        Literal(v["registermanager"]["value"])
                    )
                )
            if v.get("registerowner") is not None:
                other_properties.append(
                    Property(
                        "http://www.isotc211.org/schemas/grg/RE_RegisterOwner",
                        "Register Owner",
                        Literal(v["registerowner"]["value"])
                    )
                )
            if v.get("seeAlso") is not None:
                other_properties.append(
                    Property(
                        "http://www.w3.org/2000/01/rdf-schema#seeAlso",
                        "See Also",
                        URIRef(v["seeAlso"]["value"])
                    )
                )

            sparql_vocabs[vocab_uri] = Vocabulary(
                vocab_uri,
                vocab_uri,
                v["title"]["value"],
                v["description"].get("value") if v.get("description") is not None else None,
                v["creator"].get("value") if v.get("creator") is not None else None,
                dateutil.parser.parse(v.get("created").get("value")) if v.get("created") is not None else None,
                # dct:issued not in Vocabulary
                # dateutil.parser.parse(cs.get('issued').get('value')) if cs.get('issued') is not None else None,
                dateutil.parser.parse(v.get("modified").get("value")) if v.get("modified") is not None else None,
                v["version"].get("value") if v.get("version") is not None else None,  # versionInfo
                config.VocabSource.NvsSPARQL,  # TODO: replace this var with a reference to self class type (Source type)
                collections=str(v["t"]["value"]).split("#")[-1],
                sparql_endpoint=details["sparql_endpoint"],
                sparql_username=details.get("sparql_username"),
                sparql_password=details.get("sparql_password"),
                other_properties=other_properties
            )
            if vocab_uri == "http://vocab.nerc.ac.uk/collection/P07/current/":
                vocab_uri = "http://vocab.nerc.ac.uk/standard_name/"

                other_properties = []
                other_properties.append(
                    Property(
                        "http://purl.org/dc/terms/identifier",
                        "Identifier",
                        Literal("standard_name")
                    )
                )
                if v.get("registermanager") is not None:
                    other_properties.append(
                        Property(
                            "http://www.isotc211.org/schemas/grg/RE_RegisterManager",
                            "Register Manager",
                            Literal(v["registermanager"]["value"])
                        )
                    )
                if v.get("registerowner") is not None:
                    other_properties.append(
                        Property(
                            "http://www.isotc211.org/schemas/grg/RE_RegisterOwner",
                            "Register Owner",
                            Literal(v["registerowner"]["value"])
                        )
                    )
                if v.get("seeAlso") is not None:
                    other_properties.append(
                        Property(
                            "http://www.w3.org/2000/01/rdf-schema#seeAlso",
                            "See Also",
                            URIRef(v["seeAlso"]["value"])
                        )
                    )
                other_properties.append(
                    Property(
                        "http://www.w3.org/2000/01/rdf-schema#seeAlso",
                        "See Also",
                        URIRef("http://vocab.nerc.ac.uk/collection/P07/current/")
                    )
                )

                sparql_vocabs[vocab_uri] = Vocabulary(
                    "standard_name",
                    vocab_uri,
                    v["title"].get("value") or vocab_uri if v.get("title") else vocab_uri,
                    # Need str for sorting, not None
                    v["description"].get("value") if v.get("description") is not None else None,
                    v["creator"].get("value") if v.get("creator") is not None else None,
                    dateutil.parser.parse(v.get("created").get("value")) if v.get("created") is not None else None,
                    # dct:issued not in Vocabulary
                    # dateutil.parser.parse(cs.get('issued').get('value')) if cs.get('issued') is not None else None,
                    dateutil.parser.parse(v.get("modified").get("value")) if v.get("modified") is not None else None,
                    v["version"].get("value") if v.get("version") is not None else None,  # versionInfo
                    config.VocabSource.NvsSPARQL,
                    # TODO: replace this var with a reference to self class type (Source type)
                    collections=str(v["t"]["value"]).split("#")[-1],
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
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT DISTINCT ?c ?pl ?def ?date ?broader ?dep
                WHERE {{
                    {{?c skos:inScheme <{vocab_uri}>}}

                    ?c a skos:Concept ;
                         skos:prefLabel ?pl ;
                         skos:definition ?def ;
                         dcterms:date ?date . 
                        
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
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT DISTINCT ?c ?pl ?def ?date ?broader ?dep
                WHERE {{
                    {{?c skos:inScheme <{vocab_uri}>}}

                    ?c a skos:Concept ;
                         skos:prefLabel ?pl ;
                         skos:definition ?def ;
                         dcterms:date ?date .                         
                         
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
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT DISTINCT ?c ?pl ?def ?date ?broader ?dep
                WHERE {{
                    {{?c skos:inScheme <{vocab_uri}>}}

                    ?c a skos:Concept ;
                         skos:prefLabel ?pl ;
                         skos:definition ?def ;
                         dcterms:date ?date .

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
                concept["def"]["value"],
                concept["date"]["value"],
                concept["dep"]["value"],
                concept["broader"]["value"] if concept.get("broader") else None,
            )
            for concept in u.sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)
        ]

    def list_concepts_for_a_collection(self, acc_dep=None):
        vocab = g.VOCABS[self.vocab_uri]

        if acc_dep == "accepted":
            q = """
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?c ?pl ?def ?date ?dep
                WHERE {{
                        <{vocab_uri}> skos:member ?c .
                        
                        ?c <http://www.w3.org/2002/07/owl#deprecated> "false" .

                        OPTIONAL {{
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }}

                        ?c skos:prefLabel ?pl ;
                             skos:definition ?def ;
                             dcterms:date ?date .
                             
                        FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)
        elif acc_dep == "deprecated":
            q = """
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?c ?pl ?def ?date ?dep
                WHERE {{
                        <{vocab_uri}> skos:member ?c .
                        
                        ?c <http://www.w3.org/2002/07/owl#deprecated> "true" .

                        OPTIONAL {{
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }}

                        ?c skos:prefLabel ?pl ;
                             skos:definition ?def ;
                             dcterms:date ?date .
                             
                        FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)
        else:
            q = """
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?c ?pl ?def ?date ?dep
                WHERE {{
                        <{vocab_uri}> skos:member ?c .

                        OPTIONAL {{
                            ?c <http://www.w3.org/2002/07/owl#deprecated> ?dep .
                        }}

                        ?c skos:prefLabel ?pl ;
                            skos:definition ?def ;
                            dcterms:date ?date .
                            
                        FILTER(lang(?pl) = "{language}" || lang(?pl) = "") 
                }}
                ORDER BY ?pl
                """.format(vocab_uri=vocab.uri, language=self.language)

        return [
            (
                concept["c"]["value"],
                concept["pl"]["value"].replace("_", " "),
                concept["def"]["value"].replace("_", "_ "),
                concept["date"]["value"],
                True if concept.get("dep") and concept["dep"]["value"] == "true" else False
            )
            for concept in u.sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password)
        ]

    def list_concepts_for_standard_name(self, acc_dep=None):
        self.vocab_uri = "http://vocab.nerc.ac.uk/collection/P07/current/"
        concepts = self.list_concepts_for_a_collection(acc_dep)
        sn_concepts = []
        for concept in concepts:
            sn_concepts.append((
                "http://vocab.nerc.ac.uk/standard_name/" + concept[1].replace(" ", "_"),
                concept[1],
                concept[2],
                concept[3],
                concept[4],
            ))
        self.vocab_uri = "http://vocab.nerc.ac.uk/standard_name/"
        return sn_concepts

    def get_vocabulary(self, acc_dep=None):
        """
        Get a vocab from the cache
        :return:
        :rtype:
        """
        if self.vocab_uri == config.ABS_URI_BASE_IN_DATA + "/standard_name/":
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
            WHERE {
                <xxxx> a skos:Concept ;
                       ?p ?o .
                
                FILTER(!isLiteral(?o) || lang(?o) = "en" || lang(?o) = "")

                OPTIONAL {
                    ?o skos:prefLabel ?ropl .
                    FILTER(!isLiteral(?o) || lang(?o) = "en" || lang(?o) = "")
                }
                
                OPTIONAL {
                    ?o skos:notation ?ron
                }
            }
            """.replace("xxxx", uri)

        pl = None
        d = None
        s = {
            "provenance": None,
            "source": None,
            "wasDerivedFrom": None,
        }
        annotation_types = {
            "http://www.w3.org/2004/02/skos/core#notation": "Identifier",
            # "http://purl.org/dc/terms/identifier": "Identifier",
            "http://www.opengis.net/def/metamodel/ogc-na/status": "Status",
            'http://www.w3.org/2004/02/skos/core#altLabel': "Alternative Label",
            'http://www.w3.org/2004/02/skos/core#note': "Note",
            'http://www.w3.org/2004/02/skos/core#scopeNote': "Scope Note",
            'http://www.w3.org/2004/02/skos/core#historyNote': "History Note",
        }
        logging.debug(annotation_types.keys())
        annotations = []
        agent_types = {
            'http://purl.org/dc/terms/contributor': "Contributor",
            'http://purl.org/dc/terms/creator': "Creator",
            'http://purl.org/dc/terms/publisher': "Publisher",
        }
        agent = {}
        # sort Related instances lik this: SameAs, Broader, Related then Narrower
        related_instance_types = {
            'http://www.w3.org/2002/07/owl#sameAs': "Same As",
            'http://www.w3.org/2004/02/skos/core#broader': "Broader",
            'http://www.w3.org/2004/02/skos/core#related': "Related",
            'http://www.w3.org/2004/02/skos/core#narrower': "Narrower",
            'http://www.w3.org/2004/02/skos/core#exactMatch': "Exact Match",
            'http://www.w3.org/2004/02/skos/core#broadMatch': "Broad Match",
            'http://www.w3.org/2004/02/skos/core#closeMatch': "Close Match",
            'http://www.w3.org/2004/02/skos/core#narrowMatch': "Narrow Match",
        }
        related_instances = {}

        provenance_property_types = {
            "http://purl.org/pav/hasCurrentVersion": "Has Current Version",
            "http://purl.org/pav/version": "Version",
            "http://www.w3.org/2002/07/owl#deprecated": "Deprecated",
            "http://purl.org/pav/previousVersion": "Previous Version",
            "http://purl.org/dc/terms/isVersionOf": "Is Version Of",
            "http://purl.org/pav/authoredOn": "Authored On"
        }

        other_properties = []
        unique_alt_labels = []
        unique_versions = []
        for r in u.sparql_query(q, vocab.sparql_endpoint, vocab.sparql_username, vocab.sparql_password):
            prop = r["p"]["value"]
            val = r["o"]["value"]
            if prop == "http://www.w3.org/2004/02/skos/core#prefLabel":
                pl = val
            elif prop == "http://www.w3.org/2004/02/skos/core#definition":
                d = val
            elif prop == "http://purl.org/dc/terms/provenance":
                s["provenance"] = val
            elif prop == "http://purl.org/dc/terms/source":
                s["source"] = val
            elif prop == "http://www.w3.org/ns/prov#wasDerivedFrom":
                s["wasDerivedFrom"] = val
            elif prop in annotation_types.keys():
                if val != "":
                    annotations.append(Property(prop, annotation_types[prop], val))
            elif prop in related_instance_types.keys():
                if related_instances.get(prop) is None:
                    related_instances[prop] = {
                        "instances": [],
                        "label": related_instance_types[prop]
                    }
                # only add this instance if we don't already have one from the same vocab with the same prefLabel
                seen = False
                for ri in related_instances[prop]["instances"]:
                    if r.get("ropl") is not None:
                        if val.split("/current/")[0] in ri[0] and r["ropl"]["value"] == ri[1]:
                            seen = True

                if seen:
                    pass
                else:
                    related_instances[prop]["instances"].append(
                        (val, r["ropl"]["value"] if r.get("ropl") is not None else None)
                    )
            elif prop in provenance_property_types.keys():
                if prop == "http://purl.org/pav/hasCurrentVersion":
                    if val not in unique_versions:
                        unique_versions.append(val)
                        other_properties.append(
                            Property(prop, "Has Current Version", val))
                else:
                    other_properties.append(
                        Property(prop, provenance_property_types[prop], val.rstrip(".0")))
            elif prop == "http://www.w3.org/2004/02/skos/core#altLabel":
                if val not in unique_alt_labels:
                    unique_alt_labels.append(val)
                    other_properties.append(
                        Property(prop, "Alternative Label", val))

            # TODO: Agents

            # TODO: more Annotations

        if pl is None:
            return None

        from vocprez.model.concept import Concept

        def nvs_rel_concept_sort(s):
            for ss in s:
                if ss.startswith(config.ABS_URI_BASE_IN_DATA + "/"):
                    return "zz" + ss
                else:
                    return ss

        for i, ri in related_instances.items():
            # ri["instances"].sort(key=nvs_rel_concept_sort)
            ri["instances"].sort(key=lambda a: a[1].lower())

        def specified_order(s):
            order = [
                'http://www.w3.org/2002/07/owl#sameAs',
                'http://www.w3.org/2004/02/skos/core#broader',
                'http://www.w3.org/2004/02/skos/core#related',
                'http://www.w3.org/2004/02/skos/core#narrower',
                'http://www.w3.org/2004/02/skos/core#exactMatch',
                'http://www.w3.org/2004/02/skos/core#broadMatch',
                'http://www.w3.org/2004/02/skos/core#closeMatch',
                'http://www.w3.org/2004/02/skos/core#narrowMatch',
            ]
            return order.index(s[0])

        return Concept(
            self.vocab_uri,
            uri,
            pl,
            d,
            dict(sorted(related_instances.items(), key=lambda x: specified_order(x))),
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
