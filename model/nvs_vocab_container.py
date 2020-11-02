from flask import Response, send_from_directory, render_template
from flask_paginate import Pagination
from pyldapi import Renderer, ContainerRenderer
from rdflib import Graph, Literal, URIRef
from vocprez.model.profiles import profile_nvs
import requests


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
            profiles={"nvs": profile_nvs},
            default_profile_token=default_profile_token,
            super_register=super_register,
            page_size_max=page_size_max,
            register_template=register_template,
            **kwargs
        )

        if self.per_page == 20:
            self.per_page = 500

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
                    return self._render_nvs_profile_html()
                elif self.mediatype in Renderer.RDF_MEDIA_TYPES:
                    return self._render_nvs_profile_rdf()
                else:
                    return self._render_mem_profile_json()
            else:  # there is a paging error (e.g. page > last_page)
                return Response(self.paging_error, status=400, mimetype='text/plain')
        return response

    def _render_nvs_profile_html(self, template_context=None):
        pagination = Pagination(
            page=self.page,
            per_page=self.per_page,
            total=self.members_total_count,
            page_parameter='page', per_page_parameter='per_page'
        )
        _template_context = {
            'uri': self.instance_uri,
            'label': self.label,
            'comment': self.comment,
            'parent_container_uri': self.parent_container_uri,
            'parent_container_label': self.parent_container_label,
            'members': self.members,
            'page': self.page,
            'per_page': self.per_page,
            'first_page': self.first_page,
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'last_page': self.last_page,
            'pagination': pagination
        }
        if self.template_extras is not None:
            _template_context.update(self.template_extras)
        if template_context is not None and isinstance(template_context, dict):
            _template_context.update(template_context)

        return Response(
            render_template(
                self.members_template or 'members.html',
                **_template_context
            ),
            headers=self.headers
        )

    def _render_nvs_profile_rdf(self):
        if "/scheme/" in self.request.base_url:
            r = requests.get("$DB2RDF_SCHEMES_URI")
        else:
            r = requests.get("$DB2RDF_COLLECTIONS_URI")

        if self.mediatype in ["application/rdf+xml", "application/xml", "text/xml"]:
            return Response(
                r.text,
                mimetype=self.mediatype,
                headers=self.headers,
            )
        else:
            g = Graph().parse(data=r.text, format="xml")

            # serialise in other RDF format
            if self.mediatype in ["application/rdf+json", "application/json"]:
                graph_text = g.serialize(format="json-ld")
            else:
                graph_text = g.serialize(format=self.mediatype)

            return Response(
                graph_text,
                mimetype=self.mediatype,
                headers=self.headers,
            )
