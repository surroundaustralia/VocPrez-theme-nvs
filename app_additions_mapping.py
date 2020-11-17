

# ROUTE mapping
@app.route("/mapping/I/<string:mapping_id>/")
def mapping(mapping_id):
    from model.mapping import MappingRenderer
    return MappingRenderer(request, mapping_id).render()
# END ROUTE mapping


