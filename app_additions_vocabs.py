# ROUTE vocabs
@app.route("/vocab/")
def vocabularies(t=None, uri=None, label=None, comment=None):
    page = (
        int(request.values.get("page")) if request.values.get("page") is not None else 1
    )
    per_page = (
        int(request.values.get("per_page"))
        if request.values.get("per_page") is not None
        else 500
    )

    # get this instance's list of vocabs
    vocabs = list(g.VOCABS.keys())

    if t == "Collection":
        vocabs = [v for v in vocabs if g.VOCABS[v].collections == "Collection"]
    elif t == "ConceptScheme":
        vocabs = [v for v in vocabs if g.VOCABS[v].collections == "ConceptScheme"]

    # respond to a filter
    if request.values.get("filter") is not None:
        vocabs = [
            v for v in vocabs
            if request.values.get("filter").lower() in g.VOCABS[v].id.lower()
               or request.values.get("filter").lower() in g.VOCABS[v].title.lower()
               or request.values.get("filter").lower() in g.VOCABS[v].description.lower()
        ]

    vocabs = [(url_for("object", uri=v), g.VOCABS[v]) for v in vocabs]
    vocabs.sort(key=lambda tup: tup[1].title)
    total = len(vocabs)
    start = (page - 1) * per_page
    end = start + per_page
    vocabs = vocabs[start:end]
    logging.debug(vocabs)

    return NvsContainerRenderer(
        request,
        uri if uri is not None else config.VOCS_URI,
        label if label is not None else config.VOCS_TITLE,
        comment if comment is not None else config.VOCS_DESC,
        None,
        None,
        vocabs,
        total,
        default_profile_token="nvs",
        register_template="vocabularies.html"
    ).render()


@app.route("/collection/")
def collections():
    return vocabularies(
        t="Collection",
        uri="http://vocab.nerc.ac.uk/collection/",
        label="NVS Vocabularies",
        comment="SKOS concept collections held in the NERC Vocabulary Server. A concept collection is useful where a "
                "group of concepts shares something in common, and it is convenient to group them under a common label."
                " In the NVS, concept collections are synonymous with controlled vocabularies or code lists. Each "
                "collection is associated with its governance body. An external website link is displayed when "
                "applicable."
    )


@app.route("/scheme/")
def conceptschemes():
    return vocabularies(
        t="ConceptScheme",
        uri="http://vocab.nerc.ac.uk/scheme/",
        label="NVS Thesauri",
        comment="SKOS concept schemes managed by the NERC Vocabulary Server. A concept scheme can be viewed as an "
                "aggregation of one or more SKOS concepts. Semantic relationships (links) between those concepts may "
                "also be viewed as part of a concept scheme. A concept scheme is therefore useful for containing the "
                "concepts registered in multiple concept collections that relate to each other as a single semantic "
                "unit, such as a thesaurus."
)
# END ROUTE vocabs
