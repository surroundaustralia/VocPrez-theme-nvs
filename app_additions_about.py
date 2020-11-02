# ROUTE about
@app.route("/about")
def about():
    return render_template(
        "about.html",
    )
# END ROUTE about