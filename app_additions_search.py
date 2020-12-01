# ROUTE search
@app.route("/search")
def search():
    vs = [
        (k.replace(config.ABS_URI_BASE_IN_DATA + "/collection/", "").replace("/current/", ""), v.title)
        for k, v in g.VOCABS.items()
        if v.collections == "Collection"
    ]
    return render_template(
        "search.html",
        vocabs=sorted(vs, key=lambda tup: tup[0])
    )
# END ROUTE search
