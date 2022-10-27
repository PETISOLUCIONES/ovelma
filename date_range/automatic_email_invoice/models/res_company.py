from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    ruta_import_xml = fields.Char(string='Ruta factura xml temporal')
    sin_orden_compra = fields.Boolean(
        string="Generar acuse sin validar orden de compra",
        Help="No valida la orden de compra para generar el acuse automatico"
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sin_orden_compra = fields.Boolean(
        related='company_id.sin_orden_compra',
        string="Generar acuse sin validar orden de compra",
        Help="No valida la orden de compra para generar el acuse automatico",
        readonly=False
    )