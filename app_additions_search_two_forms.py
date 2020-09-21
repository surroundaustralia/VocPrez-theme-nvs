# ROUTE search
@app.route("/search")
def search():
    # searchables = []
    collection_searchables = []
    concept_scheme_searchables = []
    q = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT ?uri ?pl ?c
        WHERE {
            {
                ?uri a skos:ConceptScheme ;
                    skos:prefLabel ?pl .
            }
            UNION
            {
                ?uri a skos:Collection ;
                    skos:prefLabel ?pl .
            }

            ?uri a ?c
        }
        ORDER BY ?pl
        """
    for r in sparql_query(q):
        if r["c"]["value"] == "http://www.w3.org/2004/02/skos/core#Collection":
            collection_searchables.append((r["uri"]["value"], r["pl"]["value"]))
        elif r["c"]["value"] == "http://www.w3.org/2004/02/skos/core#ConceptScheme":
            concept_scheme_searchables.append((r["uri"]["value"], r["pl"]["value"]))

    if request.values.get("search"):
        last_search = request.values.get("search")
        # if request.values.get("from") and request.values.get("from") != "all":
        from_val = None
        if request.values.get("from_collection") and request.values.get("from_collection") != "all":
            from_val = request.values.get("from_collection")
            vocab_type = "http://www.w3.org/2004/02/skos/core#Collection"
        if request.values.get("from_concept_scheme") and request.values.get("from_concept_scheme") != "all":
            from_val = request.values.get("from_concept_scheme")
            vocab_type = "http://www.w3.org/2004/02/skos/core#ConceptScheme"
        if from_val is not None: # a collection or concept scheme has been selected
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

                SELECT DISTINCT ?uri ?pl (SUM(?weight) AS ?wt)
                WHERE {{
                    {{
                        ?uri skos:inScheme <{voc}> .
                        <{voc}> rdf:type <{vocType}> .
                    }}
                    UNION
                    {{
                        ?uri skos:topConceptOf <{voc}> .
                        <{voc}> rdf:type <{vocType}> .

                    }}
                    UNION
                    {{
                        <{voc}> skos:hasTopConcept ?uri .
                        <{voc}> rdf:type <{vocType}> .
                    }}
                    UNION
                    {{
                        <{voc}> skos:member ?uri .
                        <{voc}> rdf:type <{vocType}> .
                    }}

                    {{  # exact match on a prefLabel always wins
                        ?uri a skos:Concept ;
                                skos:prefLabel ?pl .
                        BIND (50 AS ?weight)
                        FILTER REGEX(?pl, "^{input}$", "i")
                    }}
                    UNION    
                    {{
                        ?uri a skos:Concept ;
                                skos:prefLabel ?pl .
                        BIND (10 AS ?weight)
                        FILTER REGEX(?pl, "{input}", "i")
                    }}
                    UNION
                    {{
                        ?uri a skos:Concept ;
                                skos:altLabel ?al ;
                                skos:prefLabel ?pl .
                        BIND (5 AS ?weight)
                        FILTER REGEX(?al, "{input}", "i")
                    }}
                    UNION
                    {{
                        ?uri a skos:Concept ;
                                skos:hiddenLabel ?hl ;
                                skos:prefLabel ?pl .
                        BIND (5 AS ?weight)
                        FILTER REGEX(?hl, "{input}", "i")
                    }}    
                    UNION
                    {{
                        ?uri a skos:Concept ;
                                skos:definition ?d ;
                                skos:prefLabel ?pl .
                        BIND (1 AS ?weight)
                        FILTER REGEX(?d, "{input}", "i")
                    }}
                }}
                GROUP BY ?uri ?pl
                ORDER BY DESC(?wt)
                """.format(**{"voc": from_val, "input": request.values.get("search"),
                              "vocType": vocab_type})
            results = []
        else:
            if request.values.get("from_collection"):
                vocab_type = "http://www.w3.org/2004/02/skos/core#Collection"
            if request.values.get("from_concept_scheme"):
                vocab_type = "http://www.w3.org/2004/02/skos/core#ConceptScheme"
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>


                SELECT DISTINCT ?voc ?uri ?pl (SUM(?weight) AS ?wt)
                WHERE {{
                    {{
                        ?uri skos:inScheme ?voc .
                        ?voc rdf:type <{vocType}> .
                    }}
                    UNION
                    {{
                        ?uri skos:topConceptOf ?voc .
                        ?voc rdf:type <{vocType}> .
                    }}
                    UNION
                    {{
                        ?voc skos:hasTopConcept ?uri .
                        ?voc rdf:type <{vocType}> .
                    }}
                    UNION
                    {{
                        ?voc skos:member ?uri .
                        ?voc rdf:type <{vocType}> .
                    }}   

                    {{  # exact match on a prefLabel always wins
                        ?uri a skos:Concept ;
                                skos:prefLabel ?pl .
                        BIND (50 AS ?weight)
                        FILTER REGEX(?pl, "^{input}$", "i")
                    }}
                    UNION    
                    {{
                        ?uri a skos:Concept ;
                                skos:prefLabel ?pl .
                        BIND (10 AS ?weight)
                        FILTER REGEX(?pl, "{input}", "i")
                    }}
                    UNION
                    {{
                        ?uri a skos:Concept ;
                                skos:altLabel ?al ;
                                skos:prefLabel ?pl .
                        BIND (5 AS ?weight)
                        FILTER REGEX(?al, "{input}", "i")
                    }}
                    UNION
                    {{
                        ?uri a skos:Concept ;
                                skos:hiddenLabel ?hl ;
                                skos:prefLabel ?pl .
                        BIND (5 AS ?weight)
                        FILTER REGEX(?hl, "{input}", "i")
                    }}    
                    UNION
                    {{
                        ?uri a skos:Concept ;
                                skos:definition ?d ;
                                skos:prefLabel ?pl .
                        BIND (1 AS ?weight)
                        FILTER REGEX(?d, "{input}", "i")
                    }}
                }}
                GROUP BY ?voc ?uri ?pl
                ORDER BY DESC(?wt)
                """.format(**{"input": request.values.get("search"),"vocType": vocab_type})
            results = {}

        for r in sparql_query(q):
            if r.get("uri") is None:
                break  # must do this check as r["weight"] will appear at least once with value 0 for no results
            # if request.values.get("from") and request.values.get("from") != "all":
            if request.values.get("from_collection") and request.values.get("from_collection") != "all":
                results.append((r["uri"]["value"], r["pl"]["value"]))
            elif request.values.get("from_concept_scheme") and request.values.get("from_concept_scheme") != "all":
                results.append((r["uri"]["value"], r["pl"]["value"]))
            else:
                if r["voc"]["value"] not in results.keys():
                    results[r["voc"]["value"]] = []
                results[r["voc"]["value"]].append((r["uri"]["value"], r["pl"]["value"]))

        return render_template(
            "search.html",
            # vocabs=searchables,
            collection_vocabs=collection_searchables,
            concept_scheme_vocabs=concept_scheme_searchables,
            last_search=last_search,
            selected_vocab=request.values.get("from"),
            vocab_type=request.values.get("vocabType"),
            results=results
        )
    else:
        return render_template(
            "search.html",
            collection_vocabs=collection_searchables,
            concept_scheme_vocabs=concept_scheme_searchables
        )


# END ROUTE search