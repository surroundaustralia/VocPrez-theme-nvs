

# ROUTE .well_known
@app.route("/.well_known/")
def well_known():
    return redirect(url_for("well_known_void"))


@app.route("/.well_known/void")
def well_known_void():
    from os.path import join
    void_file = join(config.APP_DIR, "view", "void.ttl")

    h = request.headers.get('Accept')
    f = request.args.get("_format")
    if f is not None:
        if f.startswith("application/rdf") or f.startswith("application/ld"):
            return Response(
                Graph().parse(str(void_file), format="turtle").serialize(format=f),
                mimetype=f
            )
    elif h is not None:
        if h.startswith("application/rdf") or h.startswith("application/ld"):
            return Response(
                Graph().parse(str(void_file), format="turtle").serialize(format=h),
                mimetype=h
            )

    return Response(
        open(void_file).read(),
        mimetype="text/turtle"
    )
# END ROUTE .well_known
