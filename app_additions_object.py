# ROUTE object
@app.route("/object")
def object():
    """
    This is the general RESTful endpoint and corresponding Python function to handle requests for individual objects,
    be they a Vocabulary (ConceptScheme), a Collection or Concept. Only those 3 classes of object are supported for the
    moment.

    An HTTP URI query string argument parameter 'uri' must be supplied, indicating the URI of the object being requested

    :return: A Flask Response object
    :rtype: :class:`flask.Response`
    """

    uri = request.values.get("uri")

    # must have a URI or Vocab URI supplied
    if uri is None:
        return return_vocprez_error(
            "Input Error",
            400,
            "A Query String Argument of 'uri' must be supplied for this endpoint"
        )

    if uri == config.SYSTEM_BASE_URI or uri == config.SYSTEM_BASE_URI + "/":
        return index()

    if uri == config.VOCS_URI or uri == config.VOCS_URI + "/":
        return vocabularies()

    if uri in g.VOCABS.keys():
        # get vocab details using appropriate source handler
        vocab = source.SPARQL(request).get_vocabulary(uri)
        return NvsVocabularyRenderer(request, vocab).render()

    # get the class of the object
    q = """
        SELECT DISTINCT ?c
        WHERE {
            <xxx> a ?c .
        }
        """.replace("xxx", uri)
    cs = None
    for r in u.sparql_query(q):
        if r["c"]["value"] == "http://www.w3.org/2004/02/skos/core#ConceptScheme":
            if uri in g.VOCABS.keys():
                # get vocab details using appropriate source handler
                vocab = source.SPARQL(request).get_vocabulary(uri)
                return NvsVocabularyRenderer(request, vocab).render()
            else:
                return None
        elif r["c"]["value"] == "http://www.w3.org/2004/02/skos/core#Collection":
            try:
                c = source.SPARQL(request).get_collection(uri)
                return CollectionRenderer(request, c).render()
            except:
                return None
        elif r["c"]["value"] == "http://www.w3.org/2004/02/skos/core#Concept":
            try:
                if r.get("cs"):
                    cs = r["cs"]["value"]
                c = source.SPARQL(request).get_concept(cs, uri)
                return ConceptRenderer(request, c).render()
            except:
                return None

    return return_vocprez_error(
        "Input Error",
        400,
        "The object with URI {} is not of type skos:ConceptScheme, skos:Collection or skos:Concept "
        "and only these classes of object are understood by VocPrez".format(uri)
    )
# END ROUTE object
