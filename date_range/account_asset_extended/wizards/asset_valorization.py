# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetPause(models.TransientModel):
    _name = 'account.asset.valorization'
    _description = 'Assets Valorization'

    date = fields.Date(string='Fecha', required=True, default=fields.Date.today())
    asset_id = fields.Many2one('account.asset', required=True)
    # method_number = fields.Integer(string='Number of Depreciations', required=True, compute='_compute_method')
    # method_period = fields.Selection([('1', 'Months'), ('12', 'Years')], string='Number of Months in a Period', help="The amount of time between two depreciations", related='asset_id.method_period')
    valorization_value = fields.Monetary(string="Avaluo para FISCAL", help="Valor para el avaluo", default=0)
    currency_id = fields.Many2one(related='asset_id.currency_id')
    asset_valorization_type = fields.Selection([('NIFF', 'NIFF'),('FISCAL', 'FISCAL'),('BOTH', 'AMBOS')], string='Tipo')

    # method_number_niff = fields.Integer(string='Numero de depreciaciones', required=True, compute='_compute_method')
    # method_period_niff = fields.Selection([('1', 'Months'), ('12', 'Years')], string='Number of Months in a Period', help="The amount of time between two depreciations", related='asset_id.method_period_niff')
    valorization_value_niff = fields.Monetary(string="Avaluo para NIFF", help="Valor para el avaluo", default=0)

    # profit_account_id = fields.Many2one('account.account', string='Cuenta para ganancias', help="Account used to record earnings.", store=True, related='asset_id.profit_account_id')
    # loss_account_id = fields.Many2one('account.account', string='Cuenta para perdidas', help="Account used to record losses.", store=True, related='asset_id.loss_account_id')
    profit_account_niff_id = fields.Many2one('account.account', string='Cuenta para ganancias', help="Account used to record earnings.", store=True, related='asset_id.profit_account_niff_id')
    loss_account_niff_id = fields.Many2one('account.account', string='Cuenta para perdidas', help="Account used to record losses.", store=True, related='asset_id.loss_account_niff_id')
    is_gain = fields.Boolean(default=False)
    is_lose = fields.Boolean(default=False)
    is_gain_niff = fields.Boolean(default=False)
    is_lose_niff = fields.Boolean(default=False)
    

    def Valorizar(self):
        """ 
        Valoriza el activo recalculando la tabla de amortizacion
        """
        if self.valorization_value == 0 and self.valorization_value_niff == 0:
            raise UserError(_("El valor de la valorizacion debe ser diferente a cero."))
        if self.asset_valorization_type == 'NIFF':
            self.asset_id.valorizate_asset_niff(self.valorization_value_niff, self.date)
        elif self.asset_valorization_type == 'FISCAL':
            self.asset_id.valorizate_asset(self.valorization_value, self.date)
        else:
            self.asset_id.valorizate_asset_niff(self.valorization_value_niff, self.date)
            self.asset_id.valorizate_asset(self.valorization_value, self.date)

    # @api.depends('asset_valorization_type')
    # def _compute_method(self):
    #     for record in self:
    #         record.method_number = len(record.asset_id.depreciation_move_ids.filtered(lambda moves: moves.asset_clasification == 'FISCAL' and moves.state == 'draft'))
    #         record.method_number_niff = len(record.asset_id.depreciation_move_ids.filtered(lambda moves: moves.asset_clasification == 'NIFF' and moves.state == 'draft'))
            # if record.method_number == 0:
            #     record.method_number = record.asset_id.method_number_niff - len(record.asset_id.depreciation_move_ids.filtered(lambda moves: moves.asset_clasification == 'NIFF' and moves.state == 'posted'))

    @api.onchange('valorization_value')
    def onchange_valorization_value(self):
        if self.valorization_value_niff < 0:
            self.is_gain = False
            self.is_lose = True
        elif self.valorization_value_niff > 0:
            self.is_gain = True
            self.is_lose = False
        else:
            self.is_gain = False
            self.is_lose = False