# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import tools
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    invoice_currency = fields.Boolean('Facturar en Moneda Local', compute='_get_currency_partner', readonly=False,
                                      store=True)

    @api.depends('partner_id')
    def _get_currency_partner(self):
        for sub in self:
            sub.invoice_currency = sub.partner_id.invoice_currency

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.invoice_currency:
            account_currency = self.env.user.company_id.currency_id.id
        else:
            account_currency = self.pricelist_id.currency_id.id
        if self.invoice_currency:
            invoice_vals.update({
                'currency_id': account_currency,
            })
        return invoice_vals



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.order_id.invoice_currency and self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            company = self.env.user.company_id
            currency = self.order_id.pricelist_id.currency_id
            res.update({
                'price_unit': currency._convert(self.price_unit, company.currency_id, company, self.order_id.date_order or fields.Date.today()),
            })
        return res
