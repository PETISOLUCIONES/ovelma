from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import base64
import io
from odoo.tools.misc import xlsxwriter
from odoo.http import request


class ReportInsuranseWizard(models.TransientModel):
    _name = 'report.insurance.wizard'

    type_report = fields.Selection(
        selection=[
            ('report_riesgo', 'Reporte Riesgos'),
            ('report_conciliacion', 'Reporte de Conciliación'),
            ('report_reaseguramiento', 'Reporte de Reaseguramiento'),
            ('report_reclamacion', 'Reporte de reclamacion'),
        ], string='Tipo de reporte')
    aseguradora = fields.Selection(
        selection=[
            ('mundial', 'Seguros Mundial'),
            ('bbva', 'BBVA')
        ], string='Aseguradora')

    file_import = fields.Binary("Archivo")
    file_name = fields.Char("Nombre archivo")
    fecha_ini = fields.Date(string='Fecha inicio')
    fecha_fin = fields.Date(string='Fecha fin')
    fecha_reclamacion = fields.Date(string='Fecha reclamación')
    canal_reclamacion = fields.Char(string='canal reclamacion')
    city_reclamacion_id = fields.Many2one('res.city', string='Ciudad reclamación')

    @api.model
    def create(self, vals):
        res = super(ReportInsuranseWizard, self).create(vals)
        res.crear_reporte()
        return res

    '''def write(self, vals):
        res = super(ReportInsuranseWizard, self).write(vals)
        res.crear_reporte()
        return res'''

    def crear_reporte(self):
        insurance = self.env['maintenance.equipment.insurance'].browse(self.env.context.get('active_id'))
        formato = insurance.policy_company_id.formato_aseguradora
        if formato:
            if self.type_report == 'report_riesgo':
                if formato == 'mundial':
                    self.repor_riesgo_mundial(insurance)
                elif formato == 'bbva':
                    self.repor_riesgo_bbva(insurance)
                else:
                    raise UserError("No hay reporte de riesgo para la aseguradora elegida")
            elif self.type_report == 'report_conciliacion':
                self.report_conciliacion(insurance)
            elif self.type_report == 'report_reclamacion':
                if formato == 'mundial':
                    self.report_reclamacion(insurance)
                else:
                    raise UserError("No hay reporte de reclamación para la aseguradora elegida")
            elif self.type_report == 'report_reaseguramiento':
                if formato == 'mundial':
                    self.report_reaseguramiento_mundial(insurance)
                else:
                    raise UserError("No hay reporte de reaseguramiento para la aseguradora elegida")
        else:
            raise UserError("La aseguradora no tiene un formato establecido")

    def report_reclamacion(self, seguro):
        report_name = "equipment_insurance_management.action_report_reclamación"
        filtro  = seguro.siniestros_ids.filtered(lambda l: self.fecha_ini <= l.fecha_siniestro <= self.fecha_fin)
        for rec in filtro:
            rec.write({'fecha_reclamacion': self.fecha_reclamacion,
                       'canal_reclamacion': self.canal_reclamacion,
                       'city_reclamacion_id': self.city_reclamacion_id.id, })
        pdf = self.env.ref(report_name).sudo()._render_qweb_pdf(filtro.ids)[0]
        name = self.type_report + '_' + seguro.policy_company_id.formato_aseguradora + '.pdf'
        self.file_name = name
        self.file_import = base64.b64encode(pdf)

    def report_reaseguramiento_mundial(self, seguro):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        style_row = workbook.add_format({'bg_color': '#D9E1F2'})

        partners = self.env['assets.insurance.line'].read_group([('insurance_ids', 'in', seguro.equipment_ids.ids)],
                                                                fields = ['partner_id', 'id'],
                                                             groupby=['partner_id'])

        for partner in partners:
            name_partner = self.env['res.partner'].search([('id', '=', partner['partner_id'][0])])
            worksheet = workbook.add_worksheet(name_partner.name)
            style_highlight = workbook.add_format(
                {'bold': True, 'pattern': 1, 'bg_color': '#0070C0', 'font_color': 'white'})

            headers = [
                "TIPO DE NOVEDAD",
                "NIT",
                "POLIZA",
                "SUCURSAL",
                "FECHA NOVEDAD"
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

            col = 0
            row = 0
            for header in headers:
                worksheet.write(row, col, header, style_highlight)
                worksheet.set_column(col, col, 15)
                col += 1

            for activo in seguro.equipment_ids:
                if activo.asset_id.partner_id.id == partner['partner_id'][0]:
                    row += 1
                    col = 0
                    style_row_file = style_row if row % 2 == 0 else None
                    worksheet.write(row, col, '1', style_row_file)
                    col += 1
                    worksheet.write(row, col, seguro.partner_id.vat if seguro.partner_id.vat else "", style_row_file)
                    col += 1
                    worksheet.write(row, col, seguro.policy_no if seguro.policy_no else "", style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.city_id.name if activo.city_id else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col, "", style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.asset_id.original_move_line_ids[
                        0].move_id.name if activo.asset_id.original_move_line_ids else "", style_row_file)
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
                    worksheet.write(row, col, activo.asset_id.value_residual if activo.asset_id.value_residual else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.prima if activo.prima else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.iva if activo.iva else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col,
                                    str(activo.fecha_entrega.strftime("%d/%m/%Y")) if activo.fecha_entrega else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.asset_id.partner_id.vat_num if activo.asset_id.partner_id.vat else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.asset_id.partner_id.name if activo.asset_id.partner_id.name else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.asset_id.partner_id.phone if activo.asset_id.partner_id.phone else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col,
                                    activo.asset_id.partner_id.street if activo.asset_id.partner_id.street else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col,
                                    activo.asset_id.partner_id.city_id.code if activo.asset_id.partner_id.city_id else "",
                                    style_row_file)
                    col += 1
                    worksheet.write(row, col, activo.asset_id.partner_id.vat_vd if activo.asset_id.partner_id.vat else "",
                                    style_row_file)
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
        name = self.type_report + '_' + seguro.policy_company_id.formato_aseguradora + '.xlsx'
        self.file_name = name
        self.file_import = base64.b64encode(xlsx_data)


    def report_conciliacion(self, seguro):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('REPORTE CONCILIACIÓN')
        worksheet.hide_gridlines(2)
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1,
                                               'bg_color': '#002060', 'font_color': 'white',
                                               'align': 'center', 'valign': 'center', 'border': 1})
        style_highlight2 = workbook.add_format({'bold': True, 'pattern': 1,
                                                'bg_color': '#7030A0', 'font_color': 'white',
                                                'align': 'center', 'valign': 'center'})
        money_format = workbook.add_format({'num_format': '[$$] #,##0.00', 'border': 1})
        style_highlight2.set_text_wrap()
        style_highlight.set_text_wrap()
        style_highlight2.set_align('center')
        style_highlight2.set_align('vcenter')
        style_highlight.set_align('center')
        style_highlight.set_align('vcenter')
        style_row = workbook.add_format({'border': 1})

        merge_format = workbook.add_format({
            'align': 'center'})

        # Titulo
        worksheet.merge_range('B1:O1', 'REPORTE DE DETALLE DE PRE-COBROS', merge_format)

        # Encabezado
        worksheet.merge_range('B2:C2', 'ENCABEZADO')
        worksheet.write(2, 1, 'Nombre del Tomador')
        worksheet.write(2, 2, seguro.partner_id.name)
        worksheet.write(3, 1, 'Numero de Poliza')
        worksheet.write(3, 2, seguro.policy_no)
        worksheet.write(4, 1, 'Numero de Contrato')
        worksheet.write(4, 2, '#CONTRATO')
        worksheet.write(5, 1, 'Periodo de Cobro')
        worksheet.write(5, 2, str(seguro.start_date.strftime("%d/%m/%Y")))
        worksheet.write(5, 3, str(seguro.end_date.strftime("%d/%m/%Y")))
        worksheet.write(6, 1, 'Producto')
        worksheet.write(6, 2, 'Corriente Debil Colectivo')
        worksheet.write(7, 1, 'Sub-Producto')
        worksheet.write(7, 2, 'Corriente Debil Colectivo')

        headers = ['', 'IMEI', 'ASEGURADO', 'IDENTIFICACION ASEGURADO',
                   'PERIODO DESDE', 'PERIODO HASTA', 'VALOR ASEGURADO',
                   'PRIMA', 'IMPUESTOS', 'TOTAL', 'REFERENCIA',
                   'BD SR VALOR ASEGURADO', 'BD SR PRIMA', 'BD PRIMA+IVA', 'DIFERENCIA']

        col = 0
        row = 10
        for header in headers:
            worksheet.write(row, col, header,
                            style_highlight if 0 < col < 10 else style_highlight2 if col > 9 else None)
            worksheet.set_column(col, col, 15)
            col += 1

        total_prima = 0.0
        total_impuestos = 0.0
        total = 0.0
        for activo in seguro.equipment_ids:
            row += 1
            col = 0
            worksheet.write(row, col, "")
            col += 1
            worksheet.write(row, col, activo.asset_id.serial if activo.asset_id.serial else "", style_row)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.name if activo.asset_id.partner_id.name else "", style_row)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.vat_num if activo.asset_id.partner_id.vat_num else "", style_row)
            col += 1
            worksheet.write(row, col, str(activo.fecha_inicio.strftime("%Y-%m-%d")) if activo.fecha_inicio else "", style_row)
            col += 1
            worksheet.write(row, col, str(activo.fecha_fin.strftime("%Y-%m-%d")) if activo.fecha_fin else "", style_row)
            col += 1
            worksheet.write(row, col, activo.asset_id.value_residual if activo.asset_id.value_residual else "",
                            money_format)
            col += 1
            worksheet.write(row, col, activo.prima if activo.prima else "", money_format)
            total_prima += activo.prima
            col += 1
            worksheet.write(row, col, activo.iva if activo.iva else "", money_format)
            total_impuestos += activo.iva
            col += 1
            worksheet.write(row, col, '=H' + str(row + 1) + '+I' + str(row + 1), money_format)
            col += 1
            worksheet.write(row, col, activo.asset_id.name if activo.asset_id.name else "")
            col += 1
            worksheet.write(row, col, activo.asset_id.value_residual if activo.asset_id.value_residual else "")
            col += 1
            worksheet.write(row, col, '=H' + str(row + 1) + '/G' + str(row + 1))
            col += 1
            try:
                formula = (activo.asset_id.value_residual * activo.prima / activo.asset_id.value_residual) + (
                        activo.asset_id.value_residual * activo.prima / activo.asset_id.value_residual) * activo.iva
            except ZeroDivisionError:
                formula = 0
            
            worksheet.write(row, col, formula)
            col += 1
            worksheet.write(row, col, "0")
            total += total_impuestos + total_prima

        col = 0
        row += 1
        for i in range(7):
            col += 1
            worksheet.write(row, col, "",style_highlight)

        worksheet.write(row, 1, "TOTAL", style_highlight)
        worksheet.write(row, 7, total_prima, money_format)
        worksheet.write(row, 8, total_impuestos, money_format)
        worksheet.write(row, 9, total, money_format)


        workbook.close()
        xlsx_data = output.getvalue()
        name = self.type_report + '.xlsx'
        self.file_name = name
        self.file_import = base64.b64encode(xlsx_data)

    def repor_riesgo_bbva(self, seguro):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('REPORTE SEGURO BBVA')
        style_highlight = workbook.add_format(
            {'bold': True, 'pattern': 1, 'bg_color': '#000000', 'font_color': 'white'})
        style_row = workbook.add_format({'bg_color': '#D9D9D9'})
        row = 0

        headers = [
            "ARTICULO",
            "MODELO",
            "MARCA",
            "IMEI_SERIE",
            "FECHA ENTREGA",
            "FACTURA",
            "COSTO IVA",
            "PRIMA",
            "CEDULA_CLIENTE",
            "DIGITO",
            "NOMBRES"
        ]

        col = 0
        for header in headers:
            worksheet.write(row, col, header, style_highlight)
            worksheet.set_column(col, col, 15)
            col += 1

        for activo in seguro.equipment_ids:
            row += 1
            col = 0
            style_row_file = style_row if row % 2 == 0 else None
            worksheet.write(row, col, activo.asset_id.name if activo.asset_id.name else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.model if activo.asset_id.model else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.marca if activo.asset_id.marca else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.serial if activo.asset_id.serial else "", style_row_file)
            col += 1
            worksheet.write(row, col, str(activo.fecha_entrega.strftime("%d/%m/%Y")) if activo.fecha_entrega else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.original_move_line_ids[
                0].move_id.name if activo.asset_id.original_move_line_ids else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.value_residual if activo.asset_id.value_residual else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.prima if activo.prima else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.vat_num if activo.asset_id.partner_id.vat_num else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.vat_vd if activo.asset_id.partner_id.vat_vd else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.name if activo.asset_id.partner_id.name else "",
                            style_row_file)
        workbook.close()
        xlsx_data = output.getvalue()
        name = self.type_report + '_' + seguro.policy_company_id.formato_aseguradora + '.xlsx'
        self.file_name = name
        self.file_import = base64.b64encode(xlsx_data)

    def repor_riesgo_mundial(self, seguro):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('REPORTE SEGURO')
        style_highlight = workbook.add_format(
            {'bold': True, 'pattern': 1, 'bg_color': '#70AD47', 'font_color': 'white'})
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

        for activo in seguro.equipment_ids:
            row += 1
            col = 0
            style_row_file = style_row if row % 2 == 0 else None
            worksheet.write(row, col, '1', style_row_file)
            col += 1
            worksheet.write(row, col, seguro.partner_id.vat if seguro.partner_id.vat else "", style_row_file)
            col += 1
            worksheet.write(row, col, seguro.policy_no if seguro.policy_no else "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.city_id.name if activo.city_id else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, "", style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.original_move_line_ids[
                0].move_id.name if activo.asset_id.original_move_line_ids else "", style_row_file)
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
            worksheet.write(row, col, activo.asset_id.value_residual if activo.asset_id.value_residual else "",
                            style_row_file)
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
            worksheet.write(row, col, activo.asset_id.partner_id.vat_num if activo.asset_id.partner_id.vat else "",
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
            worksheet.write(row, col,
                            activo.asset_id.partner_id.city_id.code if activo.asset_id.partner_id.city_id else "",
                            style_row_file)
            col += 1
            worksheet.write(row, col, activo.asset_id.partner_id.vat_vd if activo.asset_id.partner_id.vat else "",
                            style_row_file)
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
        name = self.type_report + '_' + seguro.policy_company_id.formato_aseguradora + '.xlsx'
        self.file_name = name
        self.file_import = base64.b64encode(xlsx_data)
