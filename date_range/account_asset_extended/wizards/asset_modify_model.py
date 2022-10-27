# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AssetPause(models.TransientModel):
    _name = 'account.asset.modify.model'
    _description = 'Asset Model Modification'

    date = fields.Date(string='Fecha de modificación', required=True, default=fields.Date.today())
    asset_id = fields.Many2one('account.asset', required=True)
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True, default=lambda self: self.env.company)
    actual_niff_model_id = fields.Many2one('account.asset', string='Modelo NIFF Actual', change_default=True, readonly=True, domain="[('company_id', '=', company_id)]")
    actual_fiscal_model_id = fields.Many2one('account.asset', string='Modelo Fiscal Actual', change_default=True, readonly=True, domain="[('company_id', '=', company_id)]")
    new_model_id = fields.Many2one('account.asset', string='Nuevo Modelo', change_default=True, domain="[('company_id', '=', company_id),('state','=','model'),('asset_type','=','purchase')]")
    model_modification_type = fields.Selection([('NIFF', 'NIFF'), ('FISCAL', 'FISCAL'), ('BOTH', 'AMBOS')], string='Tipo de cambio de modelo')
    asset_type = fields.Selection([('sale', 'Sale: Revenue Recognition'), ('purchase', 'Purchase: Asset'), ('expense', 'Deferred Expense')], index=True, related='asset_id.asset_type')
    
    def action_change_model(self):
        if self.model_modification_type == 'NIFF' and self.actual_niff_model_id == self.new_model_id:
            raise UserError(_('No puede cambiar de modelo al mismo modelo NIFF'))
        if self.model_modification_type == 'FISCAL' and self.actual_fiscal_model_id == self.new_model_id:
            raise UserError(_('No puede cambiar de modelo al mismo modelo FISCAL'))
        if self.model_modification_type == 'BOTH' and (self.actual_niff_model_id == self.new_model_id or self.actual_fiscal_model_id == self.new_model_id):
            raise UserError(_('No puede cambiar de modelo al mismo modelo'))
        childs = self.env['account.asset'].search([('asset_parent_id','=',self.asset_id.id)])
        if childs:
            for child in childs:
                self.assert_model_accounts(child, self.new_model_id)
                child.modify_model(self.model_modification_type, self.new_model_id, self.date)
        self.assert_model_accounts(self.asset_id, self.new_model_id)    
        return self.asset_id.modify_model(self.model_modification_type, self.new_model_id, self.date)


    def assert_model_accounts(self, asset, new_model):
        if not (new_model.account_asset_id
            and new_model.account_depreciation_id
            and new_model.account_depreciation_expense_id
            and new_model.journal_id
        ):
            raise UserError(_('Por favor configure las cuentas FISCALES para el modelo %s.')%(new_model.name))

        if asset.can_value and (not new_model.can_value or not new_model.profit_account_id or not new_model.loss_account_id):
            raise UserError(_('Por favor configure las cuentas para ganancias FISCALES en el modelo %s.')%(new_model.name))

        if not (new_model.account_asset_id_niff
            and new_model.account_depreciation_id_niff
            and new_model.account_depreciation_expense_id_niff
            and new_model.journal_id_niff
        ):
            raise UserError(_('Por favor configure las cuentas NIIF para el modelo %s.')%(new_model.name))

        if asset.can_value_niff and (not new_model.can_value_niff or not new_model.profit_account_niff_id or not new_model.loss_account_niff_id):
            raise UserError(_('Por favor configure las cuentas para ganancias NIIF en el modelo %s.')%(new_model.name))

        if asset.need_dismantlement and (not new_model.need_dismantlement or not new_model.dismantlement_db_account_id or not new_model.dismantlement_cr_account_id):
            raise UserError(_('Por favor configure las cuentas para desmantelamiento en el modelo %s.')%(new_model.name))

        if asset.can_value_niff and asset.is_keep_or_inversion and not new_model.can_value_niff and not new_model.is_keep_or_inversion:
            raise UserError(_('El activo %s esta configurado para estar como mantenido para la venta o propiedad de inversion, el modelo %s no tiene esta configuración.')%(asset.name, new_model.name))