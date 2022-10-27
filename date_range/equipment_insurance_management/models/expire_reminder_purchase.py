# -*- coding: utf-8 -*-

from odoo import fields, models ,api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    
    expire_reminder_days = fields.Char(
        string="Días de recordatorio de vencimiento del seguro"
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['expire_reminder_days'] =self.env['ir.config_parameter'].sudo().get_param(
            'equipment_insurance_management.expire_reminder_days', default=0
        )
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'equipment_insurance_management.expire_reminder_days', self.expire_reminder_days
            )
        return super(ResConfigSettings, self).set_values()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:       
