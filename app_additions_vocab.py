# ROUTE one vocab
# @app.route("/collection/<string:vocab_id>/<int:vocab_version>/")
# def vocabuary_version(vocab_id, vocab_version):
#     vocab_uri = None
#     for v in g.VOCABS.keys():
#         if vocab_id in v:
#             vocab_uri = v
#
#     return return_vocab2(vocab_uri, None)


@app.route("/collection/<string:vocab_id>/current/")
@app.route("/collection/<string:vocab_id>/current/<string:acc_dep>/")
def vocabulary(vocab_id, acc_dep=None):
    if acc_dep is not None:
        if acc_dep not in ["accepted", "deprecated", "all"]:
            return concept(vocab_id, acc_dep)

    def vocab_id_uri_list():
        return [(k.split("/")[-3], k) for k, v in g.VOCABS.items() if v.collections == "Collection"]

    vocab_uri = None
    for v in g.VOCABS.keys():
        if vocab_id in v:
            vocab_uri = v

    if vocab_uri is None:
        return render_template("vocabulary_404.html", id=vocab_id), 404

    return return_vocab2(vocab_uri, acc_dep)


@app.route("/scheme/<string:vocab_id>/current/")
@app.route("/scheme/<string:vocab_id>/current/<string:acc_dep>/")
def scheme(vocab_id, acc_dep=None):
    def vocab_id_uri_list():
        return [(k.split("/")[-3], k) for k, v in g.VOCABS.items() if v.collections == "Collection"]

    vocab_uri = None
    for v in g.VOCABS.keys():
        if vocab_id in v:
            vocab_uri = v

    if vocab_uri is None:
        return return_vocprez_error(
            "vocab_id not valid",
            400,
            markdown.markdown(
                "The 'vocab_id' you supplied could not be translated to a valid vocab's URI. Valid vocab_ids are:\n\n"
                "{}".format("".join(["* [{}]({})   \n".format(x[0], x[1]) for x in vocab_id_uri_list()]))
            ),
        )

    return return_vocab2(vocab_uri, acc_dep)


@app.route("/standard_name/")
def standard_name(acc_dep=None):
    return return_vocab2(config.ABS_URI_BASE_IN_DATA + "/standard_name/", acc_dep)


def return_vocab2(uri, acc_dep):
    if uri in g.VOCABS.keys():
        # get vocab details using appropriate source handler
        vocab = source.nvs_sparql.NvsSPARQL(request, language=request.values.get("lang")).get_vocabulary(acc_dep)
        return NvsVocabularyRenderer(request, vocab).render()
    else:
        return None
# END ROUTE one vocab
