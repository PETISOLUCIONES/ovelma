# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    price_unit = fields.Float('Precio Unitario', required=True, digits='Product Price')
    discount = fields.Float('Descuento (%)', digits='Discount', default=0.0)

class SaleOrderTemplateOption(models.Model):
    _inherit = "sale.order.template.option"

    price_unit = fields.Float('Precio Unitario', required=True, digits='Product Price')
    discount = fields.Float('Descuento (%)', digits='Discount')

