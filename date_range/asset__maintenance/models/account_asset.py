
from odoo import models, fields, api

class account_asset(models.Model):
    """
         Mantenimiento de activos
        """
    _inherit = ['account.asset']
    _rec_name = 'combination'

    CRITICALITY_SELECTION = [
        ('0', 'General'),
        ('1', 'Importante'),
        ('2', 'Muy importante'),
        ('3', 'Critico')
    ]
    category_ids = fields.Many2many('asset.category', id1='asset_id',
                                    id2='category_id', string='Tags')
    asset_number = fields.Char('Número del activo', size=64)
    model = fields.Char('Modelo', size=64)
    serial = fields.Char('Serial no.', size=64)
    reference = fields.Char('Referencia', size=64)
    imei = fields.Char('No. IMEI', size=64)
    marca = fields.Char('Marca', related='product_brand_id.name')
    product_brand_id = fields.Many2one(
        "product.brand", string="Marca", help="Seleccione la marca de este activo"
    )
    #user_id = fields.Many2one('res.users', 'Asignado a', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', 'Asignado a')
    property_stock_asset = fields.Many2one(
        'stock.location', "Ubicación activo",
        company_dependent=True, domain=[('usage', 'like', 'asset')],
        help="This location will be used as the destination location for installed parts during asset life.")
    criticality = fields.Selection(CRITICALITY_SELECTION, 'Criticidad')
    vendor_id = fields.Many2one('res.partner', 'Vendedor')
    manufacturer_id = fields.Many2one('res.partner', 'Fabricante')
    start_date = fields.Date('Fecha inicio')
    purchase_date = fields.Date('Fecha compra')
    warranty_start_date = fields.Date('Inicio garantía')
    warranty_end_date = fields.Date('Fin garantía')

    combination = fields.Char(string='Combination', compute='_compute_fields_combination')

    @api.depends('serial', 'name')
    def _compute_fields_combination(self):
        for test in self:
            serial = test.serial if test.serial else ''
            test.combination = '[' + serial + '] ' + test.name






