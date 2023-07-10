# Copyright 2023 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'ids_send': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    ids_send_form = fields.Html(compute="_compute_ids_send_form", sanitize=False)
    state = fields.Selection(selection_add=[("ids_send", "Send to supplier"),("purchase",)])
    partner_id = fields.Many2one(states=READONLY_STATES)

    @api.depends("order_line.product_id", "order_line.product_qty")
    def _compute_ids_send_form(self):
        for this in self:
            ids_account = this._ids_get_account()
            if not ids_account:
                this.ids_send_form = False
                continue
            cart_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n%s' % (
                self.env.ref("edi_punchout.ids_send_cart")
                .render({"object": this, "account": ids_account})
                .decode("utf8")
                .strip()
            )
            this.ids_send_form = self.env.ref("edi_punchout.ids_send_cart_form").render(
                {"account": ids_account, "cart_xml": cart_xml, "order": this}
            )

    def _ids_get_account(self):
        """
        Get IDS account for this order
        """
        self.ensure_one()
        return self.env["edi.punchout.account"].search(
            [("partner_id", "=", self.partner_id.id), ("protocol", "=", "ids")],
            limit=1,
        )

    def button_approve(self, force=False):
        """
        Set to state ids_send when approving and there is an ids account
        """
        ids_orders = self.filtered(
            lambda x: x._ids_get_account() and x.state != "ids_send"
        )
        ids_orders.write({"state": "ids_send"})
        result = super(PurchaseOrder, self-ids_orders).button_approve(force=force)
        return result
