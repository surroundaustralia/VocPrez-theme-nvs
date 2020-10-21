from flask import Response, send_from_directory
from pyldapi import Renderer, ContainerRenderer
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS
from vocprez.model.profiles import profile_nvscol


class NvsContainerRenderer(ContainerRenderer):
    def __init__(self,
                 request,
                 instance_uri,
                 label,
                 comment,
                 parent_container_uri,
                 parent_container_label,
                 members,
                 members_total_count,
                 *args,
                 profiles=None,
                 default_profile_token=None,
                 super_register=None,
                 page_size_max=1000,
                 register_template=None,
                 **kwargs):
        super().__init__(
            request,
            instance_uri,
            label,
            comment,
            parent_container_uri,
            parent_container_label,
            members,
            members_total_count,
            *args,
            profiles={"nvs": profile_nvscol},
            default_profile_token=default_profile_token,
            super_register=super_register,
            page_size_max=page_size_max,
            register_template=register_template,
            **kwargs
        )

    def render(self):
        """
        Renders the register profile.

        :return: A Flask Response object.
        :rtype: :py:class:`flask.Response`
        """
        response = super().render()
        if response is None and self.profile == 'nvs':
            if self.paging_error is None:
                if self.mediatype == 'text/html':
                    return self._render_mem_profile_html()
                elif self.mediatype in ['text/xml', 'application/xml', 'application/rdf+xml']:
                    return self._render_nvs_profile_rdf_xml()
                elif self.mediatype in Renderer.RDF_MEDIA_TYPES:
                    self.members = [(x[1].uri, x[1].title) for x in self.members]
                    return self._render_mem_profile_rdf()
                else:
                    return self._render_mem_profile_json()
            else:  # there is a paging error (e.g. page > last_page)
                return Response(self.paging_error, status=400, mimetype='text/plain')
        return response

    def _render_nvs_profile_rdf_xml(self):
        if "/scheme/" in self.request.base_url:
            return send_from_directory("/Users/nick/Work/surround/VocPrez-theme-nvs/dummy-data/", "scheme.rdf")
        else:
            return send_from_directory("/Users/nick/Work/surround/VocPrez-theme-nvs/dummy-data/", "collection.rdf")
