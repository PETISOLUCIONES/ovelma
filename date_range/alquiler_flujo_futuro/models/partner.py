from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sponsor_id = fields.Many2one('res.partner', string='Espónsor')
