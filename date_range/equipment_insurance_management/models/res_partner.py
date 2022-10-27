from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_aseguradora = fields.Boolean('Aseguradora', default=False)
    formato_aseguradora = fields.Selection(
                                selection=[
                                    ('mundial', 'Seguros Mundial'),
                                    ('bbva', 'BBVA')
                                ], string='Formato reporte')

