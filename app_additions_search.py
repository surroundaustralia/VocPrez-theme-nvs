# ROUTE search
@app.route("/search")
def search():
    if request.values.get("search"):
        last_search = request.values.get("search")
        if request.values.get("from") and request.values.get("from") != "all":
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                
                SELECT DISTINCT ?uri ?pl (SUM(?weight) AS ?wt)
                WHERE {{
                    {{
                        ?uri skos:inScheme <{voc}> .
                    }}
                    UNION
                    {{
                        ?uri skos:topConceptOf <{voc}> .
                    }}
                    UNION
                    {{
                        <{voc}> skos:hasTopConcept ?uri .
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
                """.format(**{"voc": request.values.get("from"), "input": request.values.get("search")})
            results = []
        else:
            q = """
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT DISTINCT ?voc ?uri ?pl (SUM(?weight) AS ?wt)
                WHERE {{
                    OPTIONAL {{
                        {{
                            ?uri skos:inScheme ?voc .
                        }}
                        UNION
                        {{
                            ?uri skos:topConceptOf ?voc .
                        }}
                        UNION
                        {{
                            ?voc skos:hasTopConcept ?uri .
                        }}
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
                """.format(**{"input": request.values.get("search")})
            results = {}

        for r in sparql_query(q):
            if r.get("uri") is None:
                break  # must do this check as r["weight"] will appear at least once with value 0 for no results
            if request.values.get("from") and request.values.get("from") != "all":
                results.append((r["uri"]["value"], r["pl"]["value"]))
            else:
                if r["voc"]["value"] not in results.keys():
                    results[r["voc"]["value"]] = []
                results[r["voc"]["value"]].append((r["uri"]["value"], r["pl"]["value"]))

        return render_template(
            "search.html",
            vocabs=[(v.uri, v.title) for k, v in g.VOCABS.items()],
            last_search=last_search,
            selected_vocab=request.values.get("from"),
            results=results
        )
    else:
        return render_template(
            "search.html",
            vocabs=[(v.uri, v.title) for k, v in g.VOCABS.items()]
        )
# END ROUTE search