# -*- coding: utf-8 -*-

import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class AssetModify(models.TransientModel):
    _name = 'asset.modify.massive'
    _description = 'reanudar masivamente'
    
    
    records_ids = fields.Many2many('account.asset', help='Ids usados en caso de pausar masivamente')
    # model_modify_ids = fields.Many2many('account.asset', help='Ids usados para cambiar de modelo masivamente')
    date = fields.Date(default=fields.Date.today(), string='Date')
    model_id = fields.Many2one(string="Modelo", comodel_name="account.asset",domain="[('state', '=', 'model'),('asset_type','=','purchase')]")
    is_model_change = fields.Boolean(string="¿Cambio de modelo?", default=False)

    def modify(self):
        if self.records_ids and not self.is_model_change:
            if any(self.records_ids.filtered(lambda asset: asset.state == 'draft')):
                raise UserError(_('No se puede reanudar un activo en estado Borrador'))
            for asset in self.records_ids:
                modify_obj = self.env['asset.modify'].with_context(resume_after_pause=True).create({'asset_id': asset.id, 'date': self.date, 'name': 'reanudacion masiva'})
                modify_obj.modify()
        else:
            if self.records_ids and self.is_model_change:
                for records in self.records_ids:
                    records.modify_model('BOTH',self.model_id, self.date)
                    childs = self.env['account.asset'].search([('asset_parent_id','=',records.id)])
                    if childs:
                        for child in childs:
                            child.modify_model('BOTH', self.model_id, self.date)


