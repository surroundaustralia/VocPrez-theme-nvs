# END ROUTE object


# ROUTE single concept
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>")
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>/")
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>/<string:version_no>/")
def concept(vocab_id, concept_id, version_no=None):
    # return redirect(
    #     url_for("object") + "?uri=http://vocab.nerc.ac.uk/collection/{}/current/{}/".format(vocab_id, concept_id)
    # )
    vocab_uri = "http://vocab.nerc.ac.uk/collection/{}/current/".format(vocab_id, concept_id)
    if version_no is not None:
        concept_uri = "http://vocab.nerc.ac.uk/collection/{}/current/{}/{}/".format(vocab_id, concept_id, version_no)
    else:
        concept_uri = "http://vocab.nerc.ac.uk/collection/{}/current/{}/".format(vocab_id, concept_id)

    c = getattr(source, g.VOCABS[vocab_uri].source) \
        (vocab_uri, request, language=request.values.get("lang")).get_concept(concept_uri)

    from vocprez.model.nvs_concept import NvsConceptRenderer
    return NvsConceptRenderer(request, c).render()
# END ROUTE single concept


# ROUTE about
