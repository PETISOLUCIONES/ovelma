# -*- coding: utf-8 -*-

import io
from odoo.tools.misc import xlsxwriter
from odoo.http import request
import base64

from odoo import fields, models, api, _
from datetime import datetime, time
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta



class MaintenanceEquipmentInsurance(models.Model):
    _name = "maintenance.equipment.insurance"
    _description = 'Maintenance Insurance'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Nombre",
        required=True
    )
    property_line_ids = fields.One2many(
        'insurance.property.line', 
        'insurance_id', 
        string='Línea de propiedad'
    )
    phone = fields.Char(
        string="Telefono",
        copy=True
    )
    email = fields.Char(
        string="Email",
        copy=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Titular del seguro",
        required=True,
        copy=True
    )
    contact_person = fields.Char(
        string="Persona de contacto",
    )
    policy_no = fields.Char(
        string="Numero de seguro",
        copy=False
    )
    policy_company_id = fields.Many2one(
        'res.partner',
        string="Compañía de seguros",
        copy=True,
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string="Compañía",
        default=lambda self: self.env.user.company_id,
        required=True
    )
    policy_taken = fields.Date(
        string="Fecha de emisión del seguro"
    )

    start_date = fields.Date(
        string='Comienzo del seguro',
        required=True,
        copy=False,
        tracking=True,
        default=datetime.today(),
    )
    end_date = fields.Date(
        string='Fin del seguro',
        required=True,
        copy=False,
        tracking=True,
        default=datetime.today(),
    )
    equipment_ids = fields.One2many(
        'assets.insurance.line',
        'insurance_ids',
        string="Equipo",
        required=True,
        store=True
    )

    siniestros_ids = fields.One2many(
        'assets.siniestros.line',
        'siniestros_id',
        string='siniestros'
    )

    '''asset_id = fields.Many2one('account.asset',
                               string='Activo')'''

    asset_ids = fields.Many2many('account.asset',
                               string='Activo', required=True)

    internal_notes = fields.Text(
        string='Nota interna'
    )
    amount = fields.Float(
        string='Monto del seguro',
        compute='_compute_amount',
        store=True,
        readonly=True,
        tracking=True,
    )
    responsible_user_id = fields.Many2one(
        'res.users', 
        string='Usuario responsable',
        default=lambda s: s.env.uid,
        required=True
    )
    user_id = fields.Many2one(
        'res.users', string='Creado por',
        default=lambda s: s.env.uid,
        required=True,
        readonly=True
    )
    currency_id = fields.Many2one('res.currency',
        string='Divisa',
        readonly=True, 
        default=lambda self: self.env.user.company_id.currency_id
    )
    parent_id = fields.Many2one('maintenance.equipment.insurance',
        string="Seguro anterior",
        readonly=True,
        copy=False
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            #('confirm', 'Confirmado'),
            ('in_progress', 'Confirmado'),
            ('to_expired', 'Caducará pronto'),
            ('expired', 'Caducado'),
            ('cancel', 'Cancelado'),
            ('close', 'Cerrado')
        ],
        default='draft',
        string='Estado',
        tracking=True,
        copy=False
    )

    @api.depends('equipment_ids.prima', 'equipment_ids.iva')
    def _compute_amount(self):
        for insurance in self:
            amount = 0.0
            for line in insurance.equipment_ids:
                amount += line.prima + line.iva
            insurance.amount = amount



    def create_report_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('REPORTE SEGURO')
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#70AD47', 'font_color': 'white'})
        style_row = workbook.add_format({'bg_color': '#E2EFDA'})
        style_normal = workbook.add_format({'align': 'center'})
        row = 0

        headers = [
            "TIPO DE NOVEDAD",
            "NIT",
            "POLIZA",
            "SUCURSAL",
            "LOCAL VENTA",
            "FACTURA",
            "FORMULARIO",
            "ARTICULO",
            "IMEI_SERIE",
            "MARCA",
            "MODELO",
            "PRECIO",
            "PRIMA",
            "IVA",
            "FECHA_ENTREGA",
            "CEDULA_CLIENTE",
            "NOMBRES",
            "TELEFONO",
            "DIRECCION1",
            "CIUDAD",
            "DIGITO",
            "EMAIL",
            "PLAN",
            "TIPO PRODUCTO",
        ]

        rows = []

        col = 0
        for header in headers:
            worksheet.write(row, col, header, style_highlight)
            worksheet.set_column(col, col, 15)
            col += 1

        row = 1
        col = 0
        worksheet.write(row, col, 'H', style_normal)

        for activo in self.equipment_ids:
            row += 1
            col = 0
            style_row_file = style_row if row % 2 == 0 else None
            worksheet.write(row, col, '1', style_row_file)
            col += 1
            worksheet.write(row, col, self.partner_id.vat if self.partner_id.vat else "", style_row_file)
            col += 1
            worksheet.write(row, col, self.policy_no if self.policy_no else "", style_row_file)
            col += 1
            worksheet.write(row, col, self.partner_id.city_id.name if self.partner_id.city_id else "", style_row_file)
            col += 1
            worksheet.write(row, col, "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.original_move_line_ids[0].move_id.name if activo.asset_id.original_move_line_ids else "", style_row_file)
            col += 1
            worksheet.write(row, col, "0", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.name if activo.asset_id.name else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.serial if activo.asset_id.serial else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.marca if activo.asset_id.marca else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.model if activo.asset_id.model else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.original_value if activo.asset_id.original_value else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.prima if activo.prima else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.iva if activo.iva else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, str(activo.fecha_entrega.strftime("%d/%m/%Y")) if activo.fecha_entrega else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.vat if activo.asset_id.partner_id.vat else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.name if activo.asset_id.partner_id.name else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.phone if activo.asset_id.partner_id.phone else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.street if activo.asset_id.partner_id.street else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.city_id.code if activo.asset_id.partner_id.city_id else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, "DIGITO", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.email if activo.asset_id.partner_id.email else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.plan,
                            style_row_file)
            col += 1
            worksheet.write(row, col, "3",
                            style_row_file)

        workbook.close()
        xlsx_data = output.getvalue()

        file_txt = self.env['ir.attachment'].create({
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'datas': base64.b64encode(xlsx_data),
            'name': "reporte_seguros",
            'type': 'binary'
        })
        file_id = file_txt.id
        file_name = file_txt.name

        action = {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=ir.attachment&id=" + str(
                file_id) + "&filename_field=name&field=datas&download=true&name=" + file_name,
            'target': 'new'
        }
        return action


    @api.model
    def _start_reminder(self):
        policy_days = self.env["ir.config_parameter"].sudo().get_param("equipment_insurance_management.expire_reminder_days")
        start_date=fields.Date.today() + relativedelta(days = int(policy_days))

        insurance_line = self.search([
            ('end_date','=',start_date),('state','=','in_progress')])
        for line in insurance_line:
            daily_missing_day = []
            daily_missing_day.append(start_date.strftime("%d-%m-%Y"))
            template = self.env.ref('equipment_insurance_management.equipment_insurance_management_reminder')
            template.send_mail(line.id)
            line.state='to_expired'

        insurance_line_to_expire = self.search([
            ('end_date','<=',start_date),('state','=','to_expired'), ('id','not in',insurance_line.ids)])
        insurance_line_to_expire.write({'state' :'expired'})

    # @api.multi
    def action_confirm(self):
        self.write({'state': 'in_progress'})
        return True

    # @api.multi
    def action_progress(self):
        self.write({'state': 'in_progress'})
        return True
    
    # @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True
    
    # @api.multi
    '''def action_button_equipment(self):
        self.ensure_one()
        action = self.env.ref("account_asset.action_account_asset_form").read([])[0]
        action['domain'] = [('id','=',self.asset_id.id)]
        return action'''

    # @api.multi
    def unlink(self):
        for request in self:
            if request.state not in ('draft', 'cancel'):
                raise UserError(_('No se puede eliminar un Seguro de Equipo'))
        return super(MaintenanceEquipmentInsurance, self).unlink()


    @api.onchange('policy_company_id')
    def onchange_policy_compny(self):
        if self.policy_company_id:
            self.phone = self.policy_company_id.phone
            self.email = self.policy_company_id.email

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
