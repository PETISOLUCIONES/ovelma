# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetPause(models.TransientModel):
    _inherit = 'account.asset.pause'


    asset_pause_type = fields.Selection([('NIFF', 'NIFF'),('FISCAL', 'FISCAL'),('BOTH OF THEM', 'BOTH OF THEM')])
    records_ids = fields.Many2many('account.asset', help='Ids usados en caso de pausar masivamente')

    def do_action(self):
        for record in self:
            asset_pause_type = record.asset_pause_type
            asset_ids = record.records_ids if record.records_ids else False 
            if asset_ids:
                if any(asset_ids.filtered(lambda x:  x.state != 'open')):
                    raise UserError('No se puede pausar una depreciacion que no este EN PROCESO')
                for asset in asset_ids:
                    if asset_pause_type == 'BOTH OF THEM':
                        asset.pause(pause_date=record.date)
                        asset.both_paused = True
                        asset.niff_paused = False
                        asset.fiscal_paused = False
                    else:
                        asset.pause_diferent(pause_date=record.date, asset_pause_type=asset_pause_type)
                        if asset_pause_type == 'NIFF':
                            asset.niff_paused = True
                            asset.both_paused = False
                            asset.fiscal_paused = False
                        else:
                            asset.fiscal_paused = True
                            asset.both_paused = False
                            asset.niff_paused = False
            else:
                if asset_pause_type == 'BOTH OF THEM':
                        record.asset_id.pause(pause_date=record.date)
                        record.asset_id.both_paused = True
                        record.asset_id.niff_paused = False
                        record.asset_id.fiscal_paused = False
                else:
                    record.asset_id.pause_diferent(pause_date=record.date, asset_pause_type=asset_pause_type)
                    if asset_pause_type == 'NIFF':
                        record.asset_id.niff_paused = True
                        record.asset_id.both_paused = False
                        record.asset_id.fiscal_paused = False
                    else:
                        record.asset_id.fiscal_paused = True
                        record.asset_id.both_paused = False
                        record.asset_id.niff_paused = False
