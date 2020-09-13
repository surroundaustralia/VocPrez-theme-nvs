# -*- coding: utf-8 -*-
from collections import defaultdict
from flask import Response, render_template
from flask_paginate import Pagination
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from rdflib.term import Identifier
import json
from pyldapi.renderer import Renderer, ContainerRenderer
from pyldapi.profile import Profile
from pyldapi.exceptions import ProfilesMediatypesException, CofCTtlError


class NvsCollectionsRenderer(ContainerRenderer):
    """
    Specific implementation of the abstract Renderer for displaying Register information
    """
    DEFAULT_ITEMS_PER_PAGE = 20

    def _render_mem_profile_html(self, template_context=None):
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


        return Response(
            json.dumps({
                'uri': self.instance_uri,
                'label': self.label,
                'comment': self.comment,
                'profiles': list(self.profiles.keys()),
                'default_profile': self.default_profile_token,
                'register_items': self.members
            }),
            mimetype='application/json',
            headers=self.headers
        )
