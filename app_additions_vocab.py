# ROUTE one vocab
@app.route("/collection/<string:vocab_id>/")
@app.route("/scheme/<string:vocab_id>/")
@app.route("/vocab/<string:vocab_id>/")
def vocabulary(vocab_id):
    def vocab_id_list():
        return [x.replace("/current/", "").split("#")[-1].split("/")[-1] for x in g.VOCABS.keys()]

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
                "{}".format("".join(
                    ["* [{id}]({uri})   \n".format(**{"uri": url_for("vocabulary", vocab_id=x), "id": x}) for x in
                     vocab_id_list()]))
                # "{}".format(",".join(make_vocab_id_list()))
            ),
        )

    return return_vocab(vocab_uri)
# END ROUTE one vocab
