# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetSell(models.TransientModel):
    _inherit = 'account.asset.sell'    

    date = fields.Date(string="Date", default=fields.Date.today())
    # gain_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", related='company_id.gain_account_id', help="Account used to write the journal item in case of gain", readonly=False)
    # loss_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", related='company_id.loss_account_id', help="Account used to write the journal item in case of loss", readonly=False)
    gain_account_niif_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used to write the journal item in case of gain", readonly=False)
    loss_account_niif_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used to write the journal item in case of loss", readonly=False)

    def do_action(self):
        self.ensure_one()
        invoice_line = self.env['account.move.line'] if self.action == 'dispose' else self.invoice_line_id or self.invoice_id.invoice_line_ids
        childs_ids = self.env['account.asset'].search([('asset_parent_id','=',self.asset_id.id),('state','not in',('model','draft'))]) 
        for child in childs_ids:
            if any(child.depreciation_move_ids.filtered(lambda r: r.state == 'draft' and r.date < self.date)):
                raise UserError(_('Existen asientos sin publicar en %s con una fecha menor a %s.')%(child.name, self.date))
        if self.asset_id.depreciation_move_ids.filtered(lambda r: r.state == 'draft' and r.date < self.date):
            raise UserError(_('Existen asientos sin publicar en %s con una fecha menor a %s.')%(self.asset_id.name, self.date))
        # return self.asset_id.set_to_close(invoice_line_id=invoice_line, date=invoice_line.move_id.invoice_date)
        return self.asset_id.set_to_close(invoice_line_id=invoice_line, date=self.date, gain_account=self.gain_account_id, loss_account=self.loss_account_id, gain_account_niif=self.gain_account_niif_id, loss_account_niif=self.loss_account_niif_id)


    def create(self, vals_list):
        asset_id = vals_list.get('asset_id')
        asset = self.env['account.asset'].browse(asset_id)
        vals_list['gain_account_id'] = asset.sell_gain_account_id.id
        vals_list['loss_account_id'] = asset.sell_loss_account_id.id
        vals_list['gain_account_niif_id'] = asset.sell_gain_account_niif_id.id
        vals_list['loss_account_niif_id'] = asset.sell_loss_account_niff_id.id
        return super(AssetSell, self).create(vals_list)
