# END ROUTE about


# ROUTE contact us
@app.route("/contact")
@app.route("/contact/")
@app.route("/contact-us")
@app.route("/contact-us/")
def contact_us():
    return render_template(
        "contact_us.html"
    )
# END ROUTE contact us


# ROUTE sparql
