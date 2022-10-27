# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime


class InsuranceProperty(models.Model):
    _name = "insurance.property"
    _description = 'Insurance Property'

    name = fields.Char(
        string="Nombre",
        required=True,
        copy=False
    )

class InsurancePropertyLine(models.Model):
    _name = "insurance.property.line"
    _description = 'Insurance Property'

    property_id = fields.Many2one(
        'insurance.property',
        string="Propiedad del seguro",
        required=True
    )
    insurance_id = fields.Many2one(
        'maintenance.equipment.insurance', 
        string='Seguro',
        copy=False 
    )
    value = fields.Char(
        string="Valor"
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
