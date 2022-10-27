# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from collections import Counter



class AssetSellMassive(models.TransientModel):
    _name = 'asset.sell.massive'
    _description = 'Venta masiva de activos'
    
    
    records_ids = fields.Many2many('account.asset', help='Ids usados en caso de disponer masivamente')
    move_ids = fields.Many2many('account.move', domain="[('type', '=', 'out_invoice'), ('state', '=', 'posted')]", string="Invoices")
    date = fields.Date(default=fields.Date.today(), string='Date')

    def sale(self):
        for record in self:
            if not record.move_ids:
                raise UserError(_('You have not selected any invoice.'))
            record.verify_assets(record.records_ids, record.move_ids)
            if record.records_ids:
                record.assets_validation(record.records_ids, record.date)
                vals = record.create_vals()
                for asset, invoice_line in vals:
                    gain_account_id = asset.sell_gain_account_id
                    loss_account_id = asset.sell_loss_account_id
                    gain_account_niif_id = asset.sell_gain_account_niif_id
                    loss_account_niif_id = asset.sell_loss_account_niff_id
                    asset.set_to_close(invoice_line_id=invoice_line, date=self.date, gain_account=gain_account_id, loss_account=loss_account_id, gain_account_niif=gain_account_niif_id, loss_account_niif=loss_account_niif_id)

    def assets_validation(self, records, dispose_date):
        if any(records.filtered(lambda x: x.state in ('draft','closed'))):
            raise UserError(_('Cannot sell assets in draft or close state.'))
        for asset in records:
            childs_ids = self.env['account.asset'].search([('asset_parent_id','=',asset.id),('state','not in',('model','draft'))]) 
            for child in childs_ids:
                if any(child.depreciation_move_ids.filtered(lambda r: r.state == 'draft' and r.date < dispose_date)):
                    raise UserError(_('Existen asientos sin publicar en %s con una fecha menor a %s.')%(child.name, dispose_date))
            if asset.depreciation_move_ids.filtered(lambda r: r.state == 'draft' and r.date < dispose_date):
                raise UserError(_('Existen asientos sin publicar en %s con una fecha menor a %s.')%(asset.name, dispose_date))


    def verify_assets(self, records, moves_ids):
        for asset in records:
            if (asset.asset_parent_id and asset.asset_parent_id) in records:
                raise UserError(_('You are trying to sell a principal asset and a component of the same asset on different invoice lines or diferent invoices.'))
        products = []
        for move in moves_ids:
            for line in move.invoice_line_ids:
                asset_id = self.env['account.asset'].search([('product_id','=',line.product_id.product_tmpl_id.id)])
                products.append(line.product_id) if asset_id else False
        x = Counter(products).items()
        for data in x:
            if data[1] > 1:
                raise UserError(_('You are trying to sell the same asset in diferent invoices or diferent invoice line (Product: %s).')%(data[0].name))
            



    def create_vals(self):
        result = []
        for move in self.move_ids:
            for line in move.invoice_line_ids:
                asset = self.env['account.asset'].search([('product_id','=',line.product_id.product_tmpl_id.id),('state','not in',('draft','close','model'))])
                if asset in self.records_ids:
                    result.append([asset, line])         
        return result