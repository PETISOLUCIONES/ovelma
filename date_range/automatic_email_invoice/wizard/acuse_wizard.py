from odoo import api, fields, models

class AcuseImportWizard(models.TransientModel):
    _inherit = 'acuse.import.wizard'


    @api.model
    def message_new(self, msg_dict, custom_values=None):
        acuse = super().message_new(msg_dict, custom_values=custom_values)
        return acuse


