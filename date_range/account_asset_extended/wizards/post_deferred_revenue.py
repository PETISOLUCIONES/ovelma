# -*- coding: utf-8 -*-

import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class PostDeferredRevenue(models.TransientModel):
    _name = 'post.deferred.revenue'
    _description = 'Post entries for Deferred Revenue'
    
    date = fields.Date(string="Date", default=fields.Date.today())
    unpublished_entries = fields.Integer(string='Number of unpublished enties')
    method_number = fields.Integer(string='Number of enties')
    asset_id = fields.Many2one('account.asset')

    @api.onchange('method_number')
    def _onchange_method_number(self):
        for record in self:
            if record.method_number > record.unpublished_entries:
                raise UserError(('You cannot select a value greater than the number of unpublished entries.'))

    def post(self):
        for record in self:
            moves = record.asset_id.depreciation_move_ids.filtered(lambda x: not x.reversal_move_id and x.asset_clasification == 'FISCAL' and x.state == 'draft').sorted(key=lambda l: l.date)
            to_post = moves[:record.method_number] if record.method_number < record.unpublished_entries else moves 
            for move in to_post:
                if move.auto_post:
                    move.auto_post = False
                move.date = record.date
                move.post()
            if record.method_number < record.unpublished_entries:
                moves = record.asset_id.depreciation_move_ids.filtered(lambda x: not x.reversal_move_id and x.asset_clasification == 'FISCAL' and x.state == 'draft').sorted(key=lambda l: l.date)
                post_date = record.date + relativedelta(months=+1)
                month_days = calendar.monthrange(post_date.year, post_date.month)[1]
                post_date = post_date.replace(day=month_days)
                for move in moves:
                    move.date = post_date
                    post_date += relativedelta(months=+1)
                    month_days = calendar.monthrange(post_date.year, post_date.month)[1]
                    post_date = post_date.replace(day=month_days)
