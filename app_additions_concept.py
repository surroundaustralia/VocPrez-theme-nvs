# END ROUTE object


# ROUTE single concept
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>")
@app.route("/collection/<string:vocab_id>/current/<string:concept_id>/")
def concept(vocab_id, concept_id):
    return redirect(
        url_for("object") + "?uri=http://vocab.nerc.ac.uk/collection/{}/current/{}/".format(vocab_id, concept_id)
    )
# END ROUTE single concept


# ROUTE about
