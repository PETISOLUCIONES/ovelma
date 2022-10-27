from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    sponsor_id = fields.Many2one('res.partner', related='partner_id.sponsor_id', string='Espónsor', store=True)