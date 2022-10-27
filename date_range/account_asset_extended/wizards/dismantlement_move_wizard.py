# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class DismantlementMoveWizard(models.TransientModel):

    _name = 'dismantlement.wizard'
    _description = 'Dismantlement for asset'

    amount = fields.Float(sting='Dismantlement amount', default=0)
    date = fields.Date(string='Date')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    dismantlement_db_account_id = fields.Many2one('account.account', string='Cuenta Provision DB', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    dismantlement_cr_account_id = fields.Many2one('account.account', string='Cuenta Provision CR', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    description = fields.Char(string='Descripción')
    asset_id = fields.Many2one('account.asset', string='Activo')
    company_id = fields.Many2one('res.company', string='Compañia')

    def generate_move(self):
        self.ensure_one()
        move = self.env['account.move']
        newline_vals = {}
        line_ids = []
        newline_vals['ref'] = self.asset_id.name
        newline_vals['date'] = self.date
        newline_vals['journal_id'] = self.journal_id.id
        newline_vals['asset_id'] = self.asset_id.id
        newline_vals['company_id'] = self.asset_id.company_id.id
        newline_vals['currency_id'] = self.asset_id.currency_id.id
        newline_vals['type'] = 'entry'
        newline_vals['asset_clasification'] = 'dismantlement'
        if self.amount >= 0:
            db_account = self.dismantlement_db_account_id.id
            cr_account = self.dismantlement_cr_account_id.id
        else:
            db_account = self.dismantlement_cr_account_id.id
            cr_account = self.dismantlement_db_account_id.id
        vals={
            'name': self.description if self.description else 'Dismantlement',
            'account_id': db_account,
            'debit': abs(self.amount),
            'credit': 0.0,
            'analytic_account_id': self.asset_id.account_analytic_id.id,
            'analytic_tag_ids': False,
            'currency_id': False,
            # 'partner_id': self.company_id.partner_id.id,
            'amount_currency': 0.0}
        line_ids.append((0,0,vals))
        vals={
            'name': self.description if self.description else 'Dismantlement',
            'account_id': cr_account,
            'debit': 0.0,
            'credit': abs(self.amount),
            'analytic_account_id': self.asset_id.account_analytic_id.id,
            'analytic_tag_ids': False,
            'currency_id': False,
            # 'partner_id': self.company_id.partner_id.id,
            'amount_currency': 0.0}
        line_ids.append((0,0,vals))
        newline_vals['line_ids'] = line_ids  
        moves = move.create(newline_vals)    
        self.asset_id.acumulated_dismantlement += self.amount 
        moves = self.asset_id.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'dismantlement')
        for move in moves:
            move.action_post()  
        return moves

