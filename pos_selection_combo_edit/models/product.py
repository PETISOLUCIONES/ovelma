# -*- coding: utf-8 -*-

from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_editable_items = fields.Boolean('Is items editable after confirm?')
