# END ROUTE object


# ROUTE single concept
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>")
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>/")
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>/<string:version_no>/")
def concept(vocab_id, concept_id, version_no=None):
    vocab_uri = config.ABS_URI_BASE_IN_DATA + "/collection/{}/current/".format(vocab_id, concept_id)
    if version_no is not None:
        concept_uri = config.ABS_URI_BASE_IN_DATA + "/collection/{}/current/{}/{}/".format(vocab_id, concept_id, version_no)
    else:
        concept_uri = config.ABS_URI_BASE_IN_DATA + "/collection/{}/current/{}/".format(vocab_id, concept_id)

    c = getattr(source, g.VOCABS[vocab_uri].source) \
        (request, request.values.get("lang")).get_concept(concept_uri)

    if c is None:
        return render_template("concept_404.html", uri=concept_uri), 404

    from vocprez.model.nvs_concept import NvsConceptRenderer
    return NvsConceptRenderer(request, c).render()


@app.route("/standard_name/<string:concept_id>/")
def standard_name_concept(concept_id):
    if concept_id in ["accepted", "deprecated"]:
        return standard_name(acc_dep=concept_id)

    vocab_uri = config.ABS_URI_BASE_IN_DATA + "/standard_name/"
    concept_uri = config.ABS_URI_BASE_IN_DATA + "/standard_name/{}/".format(concept_id)

    c = getattr(source, g.VOCABS[vocab_uri].source) \
        (request, request.values.get("lang")).get_concept(concept_uri)

    if c is None:
        return render_template("concept_404.html", uri=concept_uri), 404

    from vocprez.model.nvs_concept import NvsConceptRenderer
    return NvsConceptRenderer(request, c).render()
# END ROUTE single concept


# ROUTE about
