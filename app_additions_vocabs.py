# ROUTE vocabs
@app.route("/vocab/")
def vocabularies(t=None, uri=None, label=None, comment=None):
    page = (
        int(request.values.get("page")) if request.values.get("page") is not None else 1
    )
    per_page = (
        int(request.values.get("per_page"))
        if request.values.get("per_page") is not None
        else 20
    )

    # get this instance's list of vocabs
    vocabs = list(g.VOCABS.keys())

    if t == "Collection":
        vocabs = [v for v in vocabs if g.VOCABS[v].collections == "Collection"]
    elif t == "ConceptScheme":
        vocabs = [v for v in vocabs if g.VOCABS[v].collections == "ConceptScheme"]

    # respond to a filter
    if request.values.get("filter") is not None:
        vocabs = [v for v in vocabs if request.values.get("filter").lower() in g.VOCABS[v].title.lower()]

    vocabs = [(url_for("object", uri=v), g.VOCABS[v]) for v in vocabs]
    # voc_objects.sort(key=lambda tup: tup[1])
    total = len(vocabs)
    #
    # # Search
    # query = request.values.get("search")
    # results = []
    # if query:
    #     for m in match(vocabs, query):
    #         results.append(m)
    #     vocabs[:] = results
    #     vocabs.sort(key=lambda v: v.title)
    #     total = len(vocabs)
    #
    # # generate vocabs list for requested page and per_page
    start = (page - 1) * per_page
    end = start + per_page
    vocabs = vocabs[start:end]

    return ContainerRenderer(
        request,
        uri if uri is not None else config.VOCS_URI,
        label if label is not None else config.VOCS_TITLE,
        comment if comment is not None else config.VOCS_DESC,
        None,
        None,
        vocabs,
        total,
        register_template="vocabularies.html"
    ).render()


@app.route("/collection/")
def collections():
    return vocabularies(t="Collection", uri="https://vocab.nerc.ac.uk/collection/", label="NVS Collections",
                        comment="SKOS Collections managed by the NERC Vocabulary Server")


@app.route("/scheme/")
def conceptschemes():
    return vocabularies(t="ConceptScheme", uri="https://vocab.nerc.ac.uk/scheme/", label="NVS Concept Schemes",
                        comment="SKOS Concept Schemes managed by the NERC Vocabulary Server")
# END ROUTE vocabs