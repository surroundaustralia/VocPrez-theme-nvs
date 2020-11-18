

# ROUTE mapping
@app.route("/mapping/<int_ext>/<string:mapping_id>/")
def mapping(int_ext, mapping_id):
    from model.mapping import MappingRenderer
    return MappingRenderer(request, mapping_id).render()
# END ROUTE mapping


