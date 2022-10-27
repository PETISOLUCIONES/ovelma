from odoo import _, api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    facturacion_automatica = fields.Boolean(string='Facturar automaticamente', default=False)