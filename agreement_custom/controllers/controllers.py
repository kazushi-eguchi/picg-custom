# -*- coding: utf-8 -*-

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class PortalAgreement(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "agreement_count" in counters:
            agreement_model = request.env["agreement"]
            agreement_count = (
                agreement_model.search_count([])
                if agreement_model.check_access_rights("read", raise_exception=False)
                else 0
            )
            values["agreement_count"] = agreement_count
        return values

    def _agreement_get_page_view_values(self, agreement, access_token, **kwargs):
        values = {
            "page_name": "Agreements",
            "agreement": agreement,
        }
        return self._get_page_view_values(
            agreement, access_token, values, "my_agreements_history", False, **kwargs
        )

    def _get_filter_domain(self, kw):
        return []

    @http.route(
        ['/my/agreements', "/my/contracts/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_agreements(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        agreement_obj = request.env["agreement"]
        # Avoid error if the user does not have access.
        if not agreement_obj.check_access_rights("read", raise_exception=False):
            return request.redirect("/my")
        domain = self._get_filter_domain(kw)
        searchbar_sortings = {
            "date": {"label": _("Date"), "order": "start_date desc"},
            "name": {"label": _("Name"), "order": "name desc"},
            "code": {"label": _("Reference"), "order": "code desc"},
        }
        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]
        # count for pager
        agreement_count = agreement_obj.search_count(domain)

        # pager
        pager = portal_pager(
            url="/my/contracts",
            url_args={
                "start_date": date_begin,
                "end_date": date_end,
                "sortby": sortby,
            },
            total=agreement_count,
            page=page,
            step=self._items_per_page,
        )
        # content according to pager and archive selected
        agreements = agreement_obj.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session["my_agreements_history"] = agreements.ids[:100]
        values.update(
            {
                "date": date_begin,
                "agreements": agreements,
                "page_name": "Agreements",
                "pager": pager,
                "default_url": "/my/agreements",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("agreement_custom.portal_my_agreements", values)

    @http.route(
        ["/my/agreements/<int:agreement_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_agreement_detail(self, agreement_id, access_token=None, **kw):
        try:
            agreement_sudo = self._document_check_access(
                "agreement", agreement_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values = self._agreement_get_page_view_values(agreement_sudo, access_token, **kw)
        return request.render("agreement.portal_agreement_page", values)

#     @http.route('/agreement_custom/agreement_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('agreement_custom.listing', {
#             'root': '/agreement_custom/agreement_custom',
#             'objects': http.request.env['agreement_custom.agreement_custom'].search([]),
#         })

#     @http.route('/agreement_custom/agreement_custom/objects/<model("agreement_custom.agreement_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('agreement_custom.object', {
#             'object': obj
#         })
