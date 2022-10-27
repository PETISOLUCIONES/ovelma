# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_is_zero

PERIODS = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}


class AgregarLineasSuscripcion(models.Model):
    _inherit = 'sale.subscription'

    # @api.model
    '''def _recurring_create_invoice(self, automatic=False, batch_size=20):
        invoices = super(AgregarLineasSuscripcion, self)._recurring_create_invoice(automatic=automatic, batch_size=batch_size)
        for invoice in invoices:
            id_sub = invoice.invoice_line_ids.subscription_id.id
            #sale order lines of subscription not invoiceds
            so = self.env['sale.order'].search([('order_line.subscription_id', '=', id_sub),
                                                ('agregar_linea_factura', '=', True),
                                                ('invoice_status', '=', 'to invoice')], order="id desc", limit=1)
            if so:
                company = self.env.company or self.company_id
                addr = self.partner_id.address_get(['delivery', 'invoice'])
                sale_order = self.env['sale.order'].search([('order_line.subscription_id', 'in', self.ids)],
                                                           order="id desc", limit=1)
                use_sale_order = sale_order and sale_order.partner_id == self.partner_id
                partner_shipping_id = sale_order.partner_shipping_id.id if use_sale_order else self.partner_shipping_id.id or \
                                                                                               addr['delivery']
                fpos = self.env['account.fiscal.position'].with_company(company).get_fiscal_position(self.partner_id.id,
                                                                                                     partner_shipping_id)
                revenue_date_start = self.recurring_next_date
                revenue_date_stop = revenue_date_start + relativedelta(
                    **{PERIODS[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)
                invoice['invoice_line_ids'] = [(0, 0, self._prepare_invoice_line_sale_order(line, fpos, revenue_date_start, revenue_date_stop)) for
                 line in so.order_line.filtered(
                    lambda l: not float_is_zero(l.product_uom_qty, precision_rounding=l.product_id.uom_id.rounding)
                )]
                so['agregar_linea_factura'] = False
                so['invoice_status'] = 'invoiced'

        return invoices'''

    def _recurring_create_invoice(self, automatic=False, batch_size=20):
        invoices = super(AgregarLineasSuscripcion, self)._recurring_create_invoice(automatic=automatic,
                                                                                   batch_size=batch_size)
        for invoice in invoices:
            id_sub = invoice.invoice_line_ids.subscription_id.id
            # sale order lines of subscription not invoiceds
            so = self.env['sale.order'].search([('order_line.subscription_id', '=', id_sub),
                                                ('agregar_linea_factura', '=', True),
                                                ('invoice_status', '=', 'to invoice')], order="id desc", limit=1)
            if so:
                company = self.env.company or self.company_id
                addr = self.partner_id.address_get(['delivery', 'invoice'])
                sale_order = self.env['sale.order'].search([('order_line.subscription_id', 'in', self.ids)],
                                                           order="id desc", limit=1)
                use_sale_order = sale_order and sale_order.partner_id == self.partner_id
                partner_shipping_id = sale_order.partner_shipping_id.id if use_sale_order else self.partner_shipping_id.id or \
                                                                                               addr['delivery']
                fpos = self.env['account.fiscal.position'].with_company(company).get_fiscal_position(self.partner_id.id,
                                                                                                     partner_shipping_id)
                revenue_date_start = self.recurring_next_date
                revenue_date_stop = revenue_date_start + relativedelta(
                    **{PERIODS[self.recurring_rule_type]: self.recurring_interval}) - relativedelta(days=1)

                lines_invoices = []
                for line in so.order_line.filtered(
                        lambda l: not float_is_zero(l.product_uom_qty, precision_rounding=l.product_id.uom_id.rounding)
                ):
                    vals = line._prepare_invoice_line()
                    vals.update({'subscription_id': line.subscription_id.id,  #
                                 'subscription_start_date': revenue_date_start,  #
                                 'subscription_end_date': revenue_date_stop})
                    lines_invoices.append((0, 0, vals))
                invoice['invoice_line_ids'] = lines_invoices
                so['agregar_linea_factura'] = False
                so['invoice_status'] = 'invoiced'

        return invoices

    '''def _prepare_invoice_line_sale_order(self, line, fiscal_position, date_start=False, date_stop=False):
        company = self.env.company or line.analytic_account_id.company_id
        tax_ids = line.product_id.taxes_id.filtered(lambda t: t.company_id == company)
        price_unit = line.price_unit
        if fiscal_position and tax_ids:
            tax_ids = self.env['account.fiscal.position'].browse(fiscal_position).map_tax(tax_ids)
            price_unit = self.env['account.tax']._fix_tax_included_price_company(line.price_unit,
                                                                                 line.product_id.taxes_id, tax_ids,
                                                                                 self.company_id)
        return {
            'name': line.name,
            'subscription_id': line.subscription_id.id,  #
            'price_unit': price_unit or 0.0,
            'discount': line.discount,
            'quantity': line.product_uom_qty,
            'product_uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'tax_ids': [(6, 0, tax_ids.ids)],
            'analytic_account_id': line.subscription_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, line.subscription_id.tag_ids.ids)],
            'subscription_start_date': date_start,  #
            'subscription_end_date': date_stop,  #
            'sale_line_ids': [(4, line.id)],
        }'''


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agregar_linea_factura = fields.Boolean('Adicionar a la factura siguiente')
