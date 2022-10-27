# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    xdoo_allow_duplicate_product = fields.Boolean(
        string='Permitir productos duplicados',
        default=False)


    @api.constrains('order_line','xdoo_allow_duplicate_product')
    def _check_exist_product_in_line(self):
        for order in self:
            if order.xdoo_allow_duplicate_product:
                continue
            products_in_lines = order.mapped('order_line.product_id')
            for product in products_in_lines:
                lines_count = len(order.order_line.filtered(lambda line: line.product_id == product))
                if lines_count > 1:
                    raise UserError(_('Producto duplicado. %s' % (product.display_name)))
        return True
    