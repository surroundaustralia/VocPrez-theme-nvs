# ROUTE one vocab
@app.route("/collection/<string:vocab_id>/current/")
def vocabulary(vocab_id):
    def vocab_id_uri_list():
        return [(k.split("/")[-3], k) for k, v in g.VOCABS.items() if v.collections == "Collection"]

    vocab_uri = None
    for v in g.VOCABS.keys():
        if vocab_id in v:
            vocab_uri = v

    if vocab_uri is None:
        return return_vocrez_error(
            "vocab_id not valid",
            400,
            markdown.markdown(
                "The 'vocab_id' you supplied could not be translated to a valid vocab's URI. Valid vocab_ids are:\n\n"
                "{}".format("".join(["* [{}]({})   \n".format(x[0], x[1]) for x in vocab_id_uri_list()]))
            ),
        )

    return return_vocab(vocab_uri)


@app.route("/scheme/<string:vocab_id>/current/")
def scheme(vocab_id):
    def vocab_id_uri_list():
        return [(k.split("/")[-3], k) for k, v in g.VOCABS.items() if v.collections == "Collection"]

    vocab_uri = None
    for v in g.VOCABS.keys():
        if vocab_id in v:
            vocab_uri = v

    if vocab_uri is None:
        return return_vocrez_error(
            "vocab_id not valid",
            400,
            markdown.markdown(
                "The 'vocab_id' you supplied could not be translated to a valid vocab's URI. Valid vocab_ids are:\n\n"
                "{}".format("".join(["* [{}]({})   \n".format(x[0], x[1]) for x in vocab_id_uri_list()]))
            ),
        )

    return return_vocab(vocab_uri)


@app.route("/standard_name/")
def standard_name():
    return return_vocab("http://vocab.nerc.ac.uk/standard_name/")


@app.route("/standard_name/<string:concept_id>/")
def standard_name_concept(concept_id):
    vocab_uri = "http://vocab.nerc.ac.uk/standard_name/"
    concept_uri = "http://vocab.nerc.ac.uk/standard_name/{}/".format(concept_id)

    c = getattr(source, g.VOCABS[vocab_uri].source) \
        (vocab_uri, request, language=request.values.get("lang")).get_concept(concept_uri)

    from vocprez.model.nvs_concept import NvsConceptRenderer
    return NvsConceptRenderer(request, c).render()
# END ROUTE one vocab
