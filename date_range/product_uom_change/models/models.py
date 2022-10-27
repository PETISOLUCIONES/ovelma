# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    uom_temp_id = fields.Many2one(
        'uom.uom', 'Unidad temporal',
        help="Default unit of measure used for all stock operations.")

    def actualizar_unidades(self):
        res = self._cr.execute("""UPDATE
                product_template 
            SET
                uom_id = uom_temp_id WHERE uom_temp_id  IS NOT NULL RETURNING id""")
        return res
