# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import tools
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = ["sale.subscription"]

    invoice_currency = fields.Boolean('Facturar en Moneda Local', compute='_get_currency_partner', readonly=False, store=True)

    @api.depends('partner_id')
    def _get_currency_partner(self):
        for sub in self:
            sub.invoice_currency = sub.partner_id.invoice_currency

    def _prepare_invoice_data(self):
        invoice_vals = super(SaleSubscription, self)._prepare_invoice_data()
        if self.invoice_currency:
            account_currency = self.env.user.company_id.currency_id.id
        if self.invoice_currency:
            invoice_vals.update({
                'currency_id': account_currency,
            })
        return invoice_vals

    def _prepare_invoice_line(self, line, fiscal_position, date_start=False, date_stop=False):
        res = super(SaleSubscription, self)._prepare_invoice_line(line, fiscal_position, date_start=date_start, date_stop=date_stop)
        if self.invoice_currency and self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            company = self.env.user.company_id
            currency = self.pricelist_id.currency_id
            res.update({
                'price_unit': currency._convert(line.price_unit, company.currency_id, company, self.recurring_next_date or fields.Date.today()),
            })
        return res

