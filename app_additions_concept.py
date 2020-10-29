# END ROUTE object


# ROUTE single concept
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>")
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>/")
def concept(vocab_id, concept_id):
    # return redirect(
    #     url_for("object") + "?uri=http://vocab.nerc.ac.uk/collection/{}/current/{}/".format(vocab_id, concept_id)
    # )
    vocab_uri = "http://vocab.nerc.ac.uk/collection/{}/current/".format(vocab_id, concept_id)
    concept_uri = "http://vocab.nerc.ac.uk/collection/{}/current/{}/".format(vocab_id, concept_id)

    c = getattr(source, g.VOCABS[vocab_uri].source) \
        (vocab_uri, request, language=request.values.get("lang")).get_concept(concept_uri)

    from vocprez.model.nvs_concept import NvsConceptRenderer
    return NvsConceptRenderer(request, c).render()
# END ROUTE single concept


# ROUTE about
