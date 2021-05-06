# ROUTE vocabs
import markdown


@app.route("/vocab/")
def vocabularies(t=None, uri=None, label=None, description=None):
    page = (
        int(request.values.get("page")) if request.values.get("page") is not None else 1
    )
    per_page = (
        int(request.values.get("per_page"))
        if request.values.get("per_page") is not None
        else 500
    )

    # get this instance's list of vocabs
    vocab_ids = list(g.VOCABS.keys())

    if t == "Collection":
        vocabs = [v for v in vocab_ids if g.VOCABS[v].collections == "Collection"]
    elif t == "ConceptScheme":
        vocabs = [v for v in vocab_ids if g.VOCABS[v].collections == "ConceptScheme"]

    # respond to a filter
    if request.values.get("filter") is not None:
        vocabs = [
            v for v in vocab_ids
            if request.values.get("filter").lower() in g.VOCABS[v].id.lower()
               or request.values.get("filter").lower() in g.VOCABS[v].title.lower()
               or request.values.get("filter").lower() in g.VOCABS[v].description.lower()
        ]

    vocabs = [(v, g.VOCABS[v]) for v in vocabs]
    vocabs.sort(key=lambda tup: tup[1].title)
    total = len(vocabs)
    start = (page - 1) * per_page
    end = start + per_page
    vocabs = vocabs[start:end]

    return NvsContainerRenderer(
        request,
        uri if uri is not None else config.VOCS_URI,
        label if label is not None else config.VOCS_TITLE,
        description if description is not None else config.VOCS_DESC,
        None,
        None,
        vocabs,
        total,
        default_profile_token="nvs",
        register_template="vocabularies.html"
    ).render()


@app.route("/collection/")
def collections():
    return vocabularies(t="Collection")


@app.route("/scheme/")
def conceptschemes():
    return vocabularies(t="ConceptScheme")
# END ROUTE vocabs
