# -*- coding: utf-8 -*-
import logging
import binascii


from odoo import fields, http, SUPERUSER_ID, _
from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.portal.controllers import portal


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
            self, page=1, start_date=None, end_date=None, sortby=None, message=False, **kw
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
            url="/my/agreements",
            url_args={
                "start_date": start_date,
                "end_date": end_date,
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
                "date": start_date,
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
    def portal_my_agreement_detail(self, agreement_id, access_token=None, message=False, **kw):
        print(message)
        try:
            agreement_sudo = self._document_check_access(
                "agreement", agreement_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        values = self._agreement_get_page_view_values(agreement_sudo, access_token, **kw)
        values.update(
            {
                "message": message,
            }
        )
        return request.render("agreement_custom.portal_agreement_page", values)

    @http.route(
        ['/my/agreements/<int:agreement_id>/accept'],
        type='json',
        auth="public",
        website=True)
    def portal_agreement_accept(self, agreement_id, access_token=None, name=None, signature=None, **kw):
        print("cht")
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            agreement_sudo = self._document_check_access('agreement', agreement_id, access_token=access_token, **kw)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        # if not order_sudo.has_to_be_signed():
        #     return {'error': _('The order is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            agreement_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}
        # pdf = request.env.ref('sale.action_report_saleorder').with_user(SUPERUSER_ID)._render_qweb_pdf([order_sudo.id])[
        #     0]
        #
        # _message_post_helper(
        #     'sale.order', order_sudo.id, _('Order signed by %s') % (name,),
        #     attachments=[('%s.pdf' % order_sudo.name, pdf)],
        #     **({'token': access_token} if access_token else {}))

        query_string = '&message=sign_ok'

        return {
            'force_refresh': True,
            'redirect_url': agreement_sudo.get_portal_url(query_string=query_string),
        }

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
