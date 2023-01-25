import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tests import Form
from odoo.tools.translate import _


class Agreement(models.Model):
    _name = "agreement"
    _inherit = ["agreement", "portal.mixin"]

    signature = fields.Binary("signature")
    signed_by = fields.Char("Signed by")
    signed_on = fields.Datetime("Signed on")
    in_portal = fields.Boolean("In Portal")

    def _compute_access_url(self):
        for record in self:
            record.access_url = "/my/agreements/{}".format(record.id)

    def action_preview(self):
        """Invoked when 'Preview' button in contract form view is clicked."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }

    def toggle_portal(self):
        if self.in_portal:
            self.in_portal = False
            return
        if not self.in_portal:
            self.in_portal = True
            return

    def is_open(self):
        print(self.is_open)
        return self.is_open
