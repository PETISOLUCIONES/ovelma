# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    id_microsoft = fields.Char(string='ID Microsoft')
    id_CRM = fields.Char(string='ID CRM')
    fecha_cierre_facturacion = fields.Date(string="Fecha de cierre de la facturación")
    ciclo_facturacion = fields.Selection(String='Ciclo de facturación',
                                         selection=[("Anticipada", "Anticipada"), ("Vencida", "Vencida")])
