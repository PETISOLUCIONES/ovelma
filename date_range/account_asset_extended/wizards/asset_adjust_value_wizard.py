# -*- coding: utf-8 -*-

import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AdjustDepreciation(models.TransientModel):
    _name = 'asset.adjust.depreciation.wizard'
    _description = 'Adjustment for depreciation values ​​on assets'
    
    date = fields.Date(string="Date")
    asset_id = fields.Many2one('account.asset')
    method_number = fields.Integer(string='Number ofdepreciations')
    original_value = fields.Monetary(string="Original Value")
    currency_id = fields.Many2one('res.currency', string='Currency', related="asset_id.currency_id")
    company_id = fields.Many2one('res.company', string='Company', related="asset_id.company_id")
    adjust_account_id = fields.Many2one('account.account', string='Account', domain="[('company_id', '=', company_id)]")

    adjust_type = fields.Selection(
        string="Adjust Type",
        selection=[
                ('depreciation', 'Number of depreciations'),
                ('value', 'Value'),
                ('initial_date', 'Initial Date'),
        ],
    )

    def action_adjust(self):
        depreciated_amount = sum(self.asset_id.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id and x.asset_clasification == 'FISCAL').mapped('amount_total')) or 0
        if self.original_value == 0.0 or depreciated_amount >= self.original_value:
            raise UserError(('You cannot select this value for original value'))
        if self.adjust_type == 'initial_date':
            month_days = calendar.monthrange(self.date.year, self.date.month)[1]
            self.date = self.date.replace(day=month_days)
            if self.date == self.asset_id.first_depreciation_date:
                raise UserError(('You cannot select the same first depreciation date.'))
        self.asset_id.adjust_values(self.method_number, self.adjust_type, self.original_value, self.date, self.adjust_account_id)

