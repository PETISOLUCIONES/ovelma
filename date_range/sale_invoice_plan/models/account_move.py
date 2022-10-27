from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_period = fields.Char(string='Periodo')

    def create_dict_invoicehead_dian(self, move):
        invoice_head = super(AccountMove, self).create_dict_invoicehead_dian(move)
        if move.partner_id.customer_payment_mode_id.name == 'wompi' and move.partner_id.facturacion_automatica:
            invoice_head['InvoiceComment4'] = move._generate_link()
        invoice_head['InvoicePeriod'] = move.invoice_period
        return invoice_head


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cantidad_real = fields.Float(string='Cantidad', digits='Product Unit of Measure')
    cantidad_alquiler = fields.Float(string='cant alquiler', digits='Product Unit of Measure')
    rental = fields.Boolean(string='renta', default=False)