# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_asset = fields.Boolean(string="¿Aplica a activos?")