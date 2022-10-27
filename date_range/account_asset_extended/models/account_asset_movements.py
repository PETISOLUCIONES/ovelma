# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round


class AccountAssetMovements(models.Model):
    _name = 'account.asset.movements'
    _description = 'Assets movements betwen asset accounts'

    name = fields.Char(string='name', related='asset_id.name')
    asset_id = fields.Many2one('account.asset',string='Asset', store=True)
    movement_type = fields.Selection([('mantenido_venta', 'Mantenido para la venta'),('propiedad_inversion', 'Propiedad de inversion')], store=True)
    account_asset_from_id = fields.Many2one('account.account', string='Fixed Asset Account', help="Account where the asset used to be.", store=True, domain="[('company_id', '=', company_id)]")
    account_asset_to_id = fields.Many2one('account.account', string='Fixed Asset Account', help="Account where the asset used to be.", store=True, domain="[('company_id', '=', company_id)]")
    movement_date = fields.Date(string='movement date')
    reverse_date = fields.Date(string='reverse date')

    asset_movements_move_ids = fields.One2many('account.move', compute='_compute_asset_movements_move_ids', string='Movements betwen accounts', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)

    # @api.depends('asset_id')
    # def _compute_asset_movements_move_ids(self):
    #     for asset in self:
    #         move_id = self.env['account.move'].search([('asset_id','=',asset.asset_id.id),'|',('asset_clasification','=','NIFF_prop_inv'),('asset_clasification','=','NIFF_mantenido_venta')])
    #         asset.asset_movements_move_ids = move_id.ids
            