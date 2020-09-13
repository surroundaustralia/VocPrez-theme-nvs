# ROUTE collections
@app.route("/collection/")
def nvs_collections():
    page = (
        int(request.values.get("page")) if request.values.get("page") is not None else 1
    )
    per_page = (
        int(request.values.get("per_page"))
        if request.values.get("per_page") is not None
        else 20
    )

    # respond to a filter
    if request.values.get("filter") is not None:
        q = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT ?c ?pl
            WHERE {{
                ?c a skos:Collection .
                ?c skos:prefLabel ?pl .
                
                FILTER REGEX(?pl, "{}", "i")
            }}
            ORDER BY ?pl
            """.format(request.values.get("filter"))
    else:
        q = """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    
            SELECT ?c ?pl
            WHERE {
                ?c a skos:Collection .
                ?c skos:prefLabel ?pl .
            }
            ORDER BY ?pl
            """
    members = []

    for result in sparql_query(q):
        members.append((url_for("nvs_collections") + "?uri=" + result["c"]["value"], result["pl"]["value"]))

    total = len(members)
    start = (page - 1) * per_page
    end = start + per_page
    members = members[start:end]

    from vocprez.model.nvs_collections import NvsCollectionsRenderer

    return NvsCollectionsRenderer(
        request,
        "http://example.com",
        "Collections",
        "Desc of Collections",
        None,
        None,
        members,
        total
    ).render()
# END ROUTE collections
