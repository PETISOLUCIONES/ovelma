# -*- coding: utf-8 -*-

import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'
    
    both_paused = fields.Boolean(related='asset_id.both_paused', store=False)
    niff_paused = fields.Boolean(related='asset_id.niff_paused', store=False)
    fiscal_paused = fields.Boolean(related='asset_id.fiscal_paused', store=False)
    method_number_niff = fields.Integer(string='Number of Depreciations', required=True)
    method_period_niff = fields.Selection([('1', 'Months'), ('12', 'Years')], string='Number of Months in a Period', help="The amount of time between two depreciations")
    value_residual_niff = fields.Monetary(string="Depreciable Amount", help="New residual amount for the asset")
    salvage_value_niff = fields.Monetary(string="Not Depreciable Amount", help="New salvage amount for the asset")
    need_date_niff = fields.Boolean(compute="_compute_need_date_niff")
    gain_value_niff = fields.Boolean(compute="_compute_gain_value_niff", help="Technical field to know if we should display the fields for the creation of gross increase asset")
    account_asset_id_niff = fields.Many2one('account.account', string="Asset Gross Increase Account")
    account_asset_counterpart_id_niff = fields.Many2one('account.account')
    account_depreciation_id_niff = fields.Many2one('account.account')
    account_depreciation_expense_id_niff = fields.Many2one('account.account')
    asset_id = fields.Many2one(string="Asset", help="The asset to be modified by this wizard", ondelete="cascade")

    @api.depends('asset_id', 'value_residual_niff', 'salvage_value_niff')
    def _compute_need_date_niff(self):
        for record in self:
            value_changed = self.value_residual_niff + self.salvage_value_niff != self.asset_id.value_residual_niff + self.asset_id.salvage_value_niff
            record.need_date_niff = (self.env.context.get('resume_after_pause') and record.asset_id.prorata_niff) or value_changed

    @api.model
    def create(self, vals):
        if 'asset_id' in vals:
            asset = self.env['account.asset'].browse(vals['asset_id'])
            if asset.depreciation_move_ids.filtered(lambda m: m.state == 'posted' and not m.reversal_move_id and m.date > fields.Date.today()):
                raise UserError(_('Reverse the depreciation entries posted in the future in order to modify the depreciation'))
            if 'method_number_niff' not in vals:
                vals.update({'method_number_niff': len(asset.depreciation_move_ids.filtered(lambda move: move.state != 'posted' and move.asset_clasification=='NIFF')) or (asset.method_number_niff - len(asset.depreciation_move_ids.filtered(lambda move: move.state == 'posted' and move.asset_clasification=='NIFF'))) or 1})
                vals.update({'method_number_niff': (asset.method_number_niff or 1)})
            if 'method_period_niff' not in vals:
                vals.update({'method_period_niff': asset.method_period_niff})
            if 'salvage_value_niff' not in vals:
                vals.update({'salvage_value_niff': asset.salvage_value_niff})
            if 'value_residual_niff' not in vals:
                vals.update({'value_residual_niff': asset.value_residual_niff})
            if 'account_asset_id_niff' not in vals:
                vals.update({'account_asset_id_niff': asset.account_asset_id_niff.id})
            if 'account_depreciation_id_niff' not in vals:
                vals.update({'account_depreciation_id_niff': asset.account_depreciation_id_niff.id})
            if 'account_depreciation_expense_id_niff' not in vals:
                vals.update({'account_depreciation_expense_id_niff': asset.account_depreciation_expense_id_niff.id})
            if 'method_number' not in vals:
                vals.update({'method_number': (asset.method_number or 1)})
        return super(AssetModify, self).create(vals)


    def modify(self):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values, in the chatter.
        """
        for record in self:
            month_days = calendar.monthrange(record.date.year, record.date.month)[1]
            record.date = record.date.replace(day=month_days)
            if record.asset_id.fiscal_paused and not record.asset_id.niff_paused:
                date = record.asset_id.first_depreciation_date
                record.asset_id.first_depreciation_date = record.date
                method_number = self.method_number
                self.method_number = self.method_number - len(self.asset_id.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'FISCAL' and move.state == 'posted'))
                super(AssetModify,self).modify()
                self.asset_id.write({'method_number': method_number})
                record.asset_id.first_depreciation_date = date
            elif record.asset_id.niff_paused and not record.asset_id.fiscal_paused:
                date_niff = record.asset_id.first_depreciation_date_niff
                record.asset_id.first_depreciation_date_niff = record.date
                method_number = self.method_number_niff
                self.method_number_niff = self.method_number_niff - len(self.asset_id.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'NIFF' and move.state == 'posted'))
                record.modify_niff()
                record.asset_id.first_depreciation_date_niff = date_niff
                self.asset_id.write({'method_number_niff': method_number})
            else:
                date = record.asset_id.first_depreciation_date
                record.asset_id.first_depreciation_date = record.date
                date_niff = record.asset_id.first_depreciation_date_niff
                record.asset_id.first_depreciation_date_niff = record.date
                method_number = self.method_number
                method_number_niff = self.method_number_niff
                self.method_number = self.method_number - len(self.asset_id.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'FISCAL' and move.state == 'posted'))
                self.method_number_niff = self.method_number_niff - len(self.asset_id.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'NIFF' and move.state == 'posted'))
                super(AssetModify,self).modify()
                record.modify_niff()
                self.asset_id.write({'method_number': method_number})
                self.asset_id.write({'method_number_niff': method_number_niff})
                record.asset_id.first_depreciation_date = date
                record.asset_id.first_depreciation_date_niff = date_niff
            return {'type': 'ir.actions.act_window_close'}


    def modify_niff(self):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values, in the chatter.
        """
        old_values = {
            'method_number_niff': self.asset_id.method_number_niff,
            'value_residual_niff': self.asset_id.value_residual_niff,
            'salvage_value_niff': self.asset_id.salvage_value_niff,
        }

        asset_vals = {
            'method_number_niff': self.method_number_niff,
            'value_residual_niff': self.value_residual_niff,
            'salvage_value_niff': self.salvage_value_niff,
        }
        if self.need_date_niff:
            asset_vals.update({
                'first_depreciation_date_niff': self.asset_id._get_first_depreciation_date_niff(),
                'prorata_date_niff': self.date,
            })
        if self.env.context.get('resume_after_pause'):
            asset_vals.update({'state': 'open'})
            self.asset_id.message_post(body=_("Asset unpaused"))
        else:
            self = self.with_context(ignore_prorata=True)

        current_asset_book = self.asset_id.value_residual_niff + self.asset_id.salvage_value_niff
        after_asset_book = self.value_residual_niff + self.salvage_value_niff
        increase = after_asset_book - current_asset_book

        new_residual = min(current_asset_book - min(self.salvage_value_niff, self.asset_id.salvage_value_niff), self.value_residual_niff)
        new_salvage = min(current_asset_book - new_residual, self.salvage_value_niff)
        residual_increase = max(0, self.value_residual_niff - new_residual)
        salvage_increase = max(0, self.salvage_value_niff - new_salvage)

        if residual_increase or salvage_increase:
            move = self.env['account.move'].create({
                'journal_id': self.asset_id.journal_id_niff.id,
                'date': fields.Date.today(),
                'asset_clasification': 'NIFF',
                'line_ids': [
                    (0, 0, {
                        'account_id': self.account_asset_id_niff.id,
                        'debit': residual_increase + salvage_increase,
                        'credit': 0,
                        'name': _('Value increase for: ') + self.asset_id.name,
                    }),
                    (0, 0, {
                        'account_id': self.account_asset_counterpart_id_niff.id,
                        'debit': 0,
                        'credit': residual_increase + salvage_increase,
                        'name': _('Value increase for: ') + self.asset_id.name,
                    }),
                ],
            })
            move.post()
            asset_increase = self.env['account.asset'].create({
                'name': self.asset_id.name + ': ' + self.name,
                'currency_id': self.asset_id.currency_id.id,
                'company_id': self.asset_id.company_id.id,
                'asset_type': self.asset_id.asset_type,
                'method_niff': self.asset_id.method_niff,
                'method_number_niff': self.method_number_niff,
                'method_period_niff': self.method_period_niff,
                'acquisition_date_niff': self.date,
                'value_residual_niff': residual_increase,
                'salvage_value_niff': salvage_increase,
                'original_value_niff': residual_increase + salvage_increase,
                'account_asset_id_niff': self.account_asset_id_niff.id,
                'account_depreciation_id_niff': self.account_depreciation_id_niff.id,
                'account_depreciation_expense_id_niff': self.account_depreciation_expense_id.id,
                'journal_id_niff': self.asset_id.journal_id_niff.id,
                'parent_id': self.asset_id.id,
                'original_move_line_ids': [(6, 0, move.line_ids.filtered(lambda r: r.account_id == self.account_asset_id_niff).ids)],
            })
            asset_increase.validate()

            subject = _('A gross increase has been created') + ': <a href=# data-oe-model=account.asset data-oe-id=%d>%s</a>' % (asset_increase.id, asset_increase.name)
            self.asset_id.message_post(body=subject)
        if increase < 0:
            if self.env['account.move'].search([('asset_id', '=', self.asset_id.id), ('state', '=', 'draft'), ('date', '<=', self.date), ('asset_clasification', '=', 'NIFF')]):
                raise UserError('There are unposted depreciations prior to the selected operation date, please deal with them first.')
            move = self.env['account.move'].create(self.env['account.move']._prepare_move_for_asset_depreciation_niff({
                'amount': -increase,
                'asset_id': self.asset_id,
                'move_ref': _('Value decrease for: ') + self.asset_id.name,
                'date': self.date,
                'asset_remaining_value': 0,
                'asset_depreciated_value': 0,
                'asset_value_change': True,
            })).post()

        asset_vals.update({
            'value_residual_niff': new_residual,
            'salvage_value_niff': new_salvage,
        })
        self.asset_id.write(asset_vals)
        self.asset_id.compute_depreciation_board_niff()
        self.asset_id.children_ids.write({
            'method_number_niff': asset_vals['method_number_niff'],
            # 'method_period_niff': asset_vals['method_period_niff'],
        })
        for child in self.asset_id.children_ids:
            child.compute_depreciation_board()
        tracked_fields = self.env['account.asset'].fields_get(old_values.keys())
        changes, tracking_value_ids = self.asset_id._message_track(tracked_fields, old_values)
        if changes:
            self.asset_id.message_post(body=_('Depreciation board modified') + '<br>' + self.name, tracking_value_ids=tracking_value_ids)
        # return {'type': 'ir.actions.act_window_close'}


    @api.depends('asset_id', 'value_residual_niff', 'salvage_value_niff')
    def _compute_gain_value_niff(self):
        for record in self:
            record.gain_value_niff = record.value_residual_niff + record.salvage_value_niff > record.asset_id.value_residual_niff + record.asset_id.salvage_value_niff

    # @api.depends('asset_id', 'value_residual', 'salvage_value')
    # def _compute_gain_value(self):
    #     for record in self:
    #         record.gain_value = record.value_residual + record.salvage_value > record.asset_id.value_residual + record.asset_id.salvage_value
