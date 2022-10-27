# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EquipmentInsuranceWizard(models.TransientModel):
    _name = "maintenance.equipment.insurance.wizard"


    start_date = fields.Date(
        string='Renovar Inicio',
        default=fields.Date.today(), 
        required=True
    )
    end_date = fields.Date(
        string='Renovar Fin',
        required=True
    )

   
    # @api.multi
    def action_create_renew(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        policy = self.env[active_model].browse(active_ids)
        
        policy_move = policy.copy(default={
             'start_date': self.start_date,
             'end_date': self.end_date,
             'parent_id':policy.id,
        })

        for line in policy.property_line_ids :
            line.copy(default={
                 'insurance_id': policy_move.id,
            })
        for line in policy.equipment_ids:
            line.copy(default={
                'insurance_ids': policy_move.id,
                'prima': line.prima - line.asset_id.residual_value * line.prima / 100
            })


        action = self.env.ref('equipment_insurance_management.action_equipment_insurance_view').sudo().read()[0]
        action['domain'] = [('id','=',policy_move.id)]
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:       
 

 
       
      





            

        


