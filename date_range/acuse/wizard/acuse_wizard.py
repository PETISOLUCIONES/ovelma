from odoo import models, fields, api, _
import requests
import base64
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import json
from datetime import datetime


class AcuseImportWizard(models.TransientModel):
    _name = 'acuse.import.wizard'
    _description = 'cargar archivos acuse'

    file_import = fields.Binary("Archivo")
    file_name = fields.Char("Nombre archivo")

    def enviar_archivo(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        move = self.env[active_model].browse(active_ids)
        ip_ws = str(move.company_id.ip_webservice)
        url = 'http://' + ip_ws + '/api/EventosFacturacion?num_fact=' + move.name
        #url = 'http://localhost:57780/api/EventosFacturacion?num_fact='+ move.name

        headers = {'content-type': 'text/xml;charset=utf-8'}
        deco = base64.b64decode(self.file_import)
        responsews = requests.post(url, data=deco, headers=headers)
        if responsews.status_code == 200:
            respuesta_str = responsews.content.decode('utf-8')
            respuesta = json.loads(respuesta_str)
            if respuesta['estado'] == 'exitoso':
                move.write({'estado_acuse': respuesta['codigo']})
                self.env['account.acuse'].create({
                    'cude': respuesta['cude'],
                    'fecha_evento':  respuesta["fecha_evento"],
                    'name':  respuesta['numero_evento'],
                    'move_id': move.id,
                    'codigo': respuesta['codigo'],
                })
            else:
                raise UserError(respuesta['Respuesta'])
        elif responsews.status_code == 500:
            raise UserError("Error en la conexión al Web service")
        return True

