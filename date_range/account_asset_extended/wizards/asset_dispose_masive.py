# -*- coding: utf-8 -*-

import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class AssetDisposeMasive(models.TransientModel):
    _name = 'asset.dispose.massive'
    _description = 'disposicion masiva de activos'
    
    
    records_ids = fields.Many2many('account.asset', help='Ids usados en caso de disponer masivamente')
    # model_modify_ids = fields.Many2many('account.asset', help='Ids usados para cambiar de modelo masivamente')
    date = fields.Date(default=fields.Date.today(), string='Date')

    def dispose(self):
        for record in self:
            if record.records_ids:
                record.assets_organization(record.records_ids)
                record.assets_validation(record.records_ids, record.date)
                for asset in record.records_ids:
                    sell = self.env['account.asset.sell'].create({'asset_id': asset.id, 'action': 'dispose', 'date': record.date})
                    sell.do_action()

    def assets_validation(self, records, dispose_date):
        if any(records.filtered(lambda x: x.state in ('draft','closed'))):
            raise UserError(_('Cannot dispose assets in draft or close state.'))
        for asset in records:
            childs_ids = self.env['account.asset'].search([('asset_parent_id','=',asset.id),('state','not in',('model','draft'))]) 
            for child in childs_ids:
                if any(child.depreciation_move_ids.filtered(lambda r: r.state == 'draft' and r.date < dispose_date)):
                    raise UserError(_('Existen asientos sin publicar en %s con una fecha menor a %s.')%(child.name, dispose_date))
            if asset.depreciation_move_ids.filtered(lambda r: r.state == 'draft' and r.date < dispose_date):
                raise UserError(_('Existen asientos sin publicar en %s con una fecha menor a %s.')%(asset.name, dispose_date))

    def assets_organization(self, records):
        asset_ids = self.records_ids.ids
        remove_ids = []
        for asset in records:
            if asset.asset_parent_id and asset.asset_parent_id in records:
                remove_ids.append(asset.id)
        for remove in remove_ids:
            asset_ids.remove(remove)
        self.records_ids = asset_ids