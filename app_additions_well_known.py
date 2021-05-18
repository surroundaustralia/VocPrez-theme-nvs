

# ROUTE .well_known
@app.route("/.well_known/")
def well_known():
    return redirect(url_for("well_known_void"))


@app.route("/.well_known/void")
def well_known_void():
    void = """

    """
    return Response(
        void,
        mimetype="text/turtle"
    )
# END ROUTE .well_known
