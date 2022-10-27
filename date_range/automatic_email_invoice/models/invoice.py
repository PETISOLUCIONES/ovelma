from odoo import api, fields, models, _
# from lxml import etree
import base64
import zipfile
import os
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import xml.etree.ElementTree as ET

NSMAP = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ccts": "urn:un:unece:uncefact:documentation:2",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
    "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2",
    "sac": "urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1",
    "udt": "urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

NSMAP_firmada = {"ds": "http://www.w3.org/2000/09/xmldsig#",
                 "xades": "http://uri.etsi.org/01903/v1.3.2#",
                 "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
                 "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
                 "xades141": "http://uri.etsi.org/01903/v1.4.1#",
                 "sts": "dian:gov:co:facturaelectronica:Structures-2-1",
                 "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
                 "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                 "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
                 }


class Invoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        flag = False
        for attachment in msg_dict['attachments']:
            name = attachment.fname
            if name.find(".zip") != -1:
                content = attachment.content
                if self.env.company.ruta_import_xml:
                    ruta = self.env.company.ruta_import_xml + '/'
                else:
                    ruta = 'temporal/'

                full_file = os.path.abspath(os.path.join('', ruta))
                if not os.path.exists(full_file):
                    os.makedirs(full_file)

                with open(full_file + "/" + name, "wb") as tmp:
                    tmp.write(content)
                    name_zip = full_file + "/" + name

                if zipfile.is_zipfile(name_zip) and flag == False:
                    with zipfile.ZipFile(name_zip, 'r') as obj_zip:
                        FileNames = obj_zip.namelist()
                        for fileName in FileNames:
                            if fileName.endswith('.xml'):

                                xml = obj_zip.read(fileName).decode("utf-8")
                                # archivo = base64.b64decode(xml).decode("utf-8")
                                try:
                                    attach = ET.ElementTree(ET.fromstring(xml))

                                except:
                                    raise ValidationError('Error al leer el xml')

                                firmadaText = attach.find('.//cac:Attachment/cac:ExternalReference/cbc:Description',
                                                          namespaces=NSMAP_firmada)
                                firm_et = ET.ElementTree(ET.fromstring(firmadaText.text))

                                factura_valida = self.validar_factura(firm_et, msg_dict['subject'])
                                if factura_valida['valida']:
                                    # obj_zip.extract(fileName, full_file + '/')
                                    invoice = self.cargar_archivo_xml(firm_et)
                                    journal = self.env["account.journal"].search([('type', '=', 'purchase')], limit=1).id
                                    invoice_parameters = {'move_type': invoice["move_type"], 'journal_id': journal}
                                    move = super(Invoice, self).message_new(msg_dict, custom_values=invoice_parameters)
                                    flag = True
                                    move.write(invoice)
                                    if invoice["purchase_id"]:
                                        ls_invoices = self.env["purchase.order"].search(
                                            [('id', '=', invoice["purchase_id"].id)]).invoice_ids.ids

                                        purchase_order = self.env["purchase.order"].search(
                                            [('id', '=', invoice["purchase_id"].id)]).write({'invoice_ids': [(4, move.id)],
                                                                                             'invoice_count': len(
                                                                                                 ls_invoices) + 1,
                                                                                             'invoice_status': 'invoiced'})
                                        if move.comparar_factura_compra(move, invoice["purchase_id"]):
                                            move.action_post()
                                            encoded = xml.encode("utf-8")
                                            move.write({'attachment_ids': [(0, 0,{
                                                                                    'name':fileName,
                                                                                    'type': 'binary',
                                                                                    'res_id': move.id,
                                                                                    'res_model': 'account.move',
                                                                                    'datas': base64.b64encode(encoded),
                                                                                    'mimetype': 'application/xml'
                                                                                })]})
                                            move.EnviarAcuse()
                                    elif move.company_id.sin_orden_compra:
                                        move.action_post()
                                        encoded = xml.encode("utf-8")
                                        move.write({'attachment_ids': [(0, 0, {
                                            'name': fileName,
                                            'type': 'binary',
                                            'res_id': move.id,
                                            'res_model': 'account.move',
                                            'datas': base64.b64encode(encoded),
                                            'mimetype': 'application/xml'
                                        })]})
                                        move.EnviarAcuse()

                                    if os.path.exists(full_file + '/' + fileName):
                                        os.remove(full_file + '/' + fileName)
                                else:
                                    self.enviar_correo_rechazo(firm_et, factura_valida['mensaje'])
                            else:
                                flag = True
                                move = super(Invoice, self).message_new(msg_dict, custom_values=custom_values)
                if os.path.exists(name_zip):
                    os.remove(name_zip)

        if not flag:
            move = super(Invoice, self).message_new(msg_dict, custom_values=custom_values)

        return move


    def enviar_correo_rechazo(self, firmada, errores):
        email_facturador = firmada.find(".//cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:ElectronicMail",
                                      namespaces=NSMAP_firmada).text
        nom_facturador = firmada.find(
            ".//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:RegistrationName",
            namespaces=NSMAP_firmada).text

        detalles = ""
        for error in errores:
            detalles += "<br/> " + error

        body = '''
            <b>Estimado ''' " %s</b>," % (nom_facturador) + '''
            <br/><br/><br/><p>Le notificamos que se ha recibido el documento con el siguiente detalle:</p>
            <br/><br/><br/><p>Observaciones: </p>
            <br/><br/> ''' + detalles + '''
            <br/><br/><br/><p>Para mas información por favor comunicarse con su proveedor tecnológico</p>
        '''
        self.env.ref('automatic_email_invoice.email_template_invoice_rechazo').send_mail(
            self.id, notif_layout="mail.mail_notification_light",
            force_send=True,
            email_values={
                'email_to': email_facturador ,
                'email_from': self.env.user.company_id.email_formatted,
                'body_html': body,
            },
        )

    def validar_asunto(self,firmada, asunto):
        list_asunto = asunto.split(';')
        nit_facturador = firmada.find(".//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
                                      namespaces=NSMAP_firmada).text
        nom_facturador = firmada.find(".//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:RegistrationName",
                                      namespaces=NSMAP_firmada).text
        num_factura = firmada.find(".//cbc:ID", namespaces=NSMAP_firmada).text
        tipo_factura = firmada.find(".//cbc:InvoiceTypeCode", namespaces=NSMAP_firmada).text
        nom_comercial_fact = firmada.find(".//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name",
                                          namespaces=NSMAP_firmada).text
        if not list_asunto[0] == nit_facturador or not list_asunto[1] == nom_facturador or not list_asunto[2] == num_factura or not list_asunto[3] == tipo_factura or not(list_asunto[4] == nom_comercial_fact or list_asunto[4] == nom_facturador):
            return False
        return True

    def validar_nitempresa(self, firmada):
        numero_empresa = firmada.find(".//cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID", namespaces=NSMAP_firmada)
        nit_empresa = numero_empresa.text.strip()
        if not nit_empresa == self.GetNitCompany(self.env.user.company_id.vat):
            return False
        return True

    def validar_factura(self, firmada, asunto):
        mensaje = []
        result = {'valida': True,
                  'mensaje': mensaje}
        if not self.validar_asunto(firmada, asunto):
            mensaje.append("- El asunto del correo no cumple con la estructura DIAN esperada.")
            result['valida'] = False
        if not self.validar_nitempresa(firmada):
            mensaje.append("- El nit que se encuentra en el XML no corresponde a la empresa " + self.env.user.company_id.name)
            result['valida'] = False
        result['mensaje'] = mensaje
        return result


    def buscar_producto(self, product_name, proveedor):
        product_product = self.env['product.product'].search([('name', '=ilike', product_name)])
        if product_product:
            result = {'product_id': product_product.id,
                      'product_name': product_name,
                      'product_uom_id': product_product.uom_id}
        else:
            product_suplier = self.env['product.supplierinfo'].search(
                [('product_name', '=ilike', product_name), ('name.vat_num', '=', proveedor)])
            if product_suplier:
                result = {'product_id': product_suplier.product_tmpl_id.product_variant_id.id,
                          'product_name': product_name,
                          'product_uom_id': product_suplier.product_tmpl_id.product_variant_id.uom_id}
            else:
                result = {'product_id': False,
                          'product_name': product_name,
                          'product_uom_id': False}
        return result

    def comparar_factura_compra(self, factura, compra):
        iguales = True
        if factura.partner_id != compra.partner_id:
            iguales = False
        for line in factura.invoice_line_ids:
            if line.product_id:
                product_in_compra = self.env['purchase.order.line'].search([('id', 'in', compra.order_line.ids),
                                                                            ('product_id', '=', line.product_id.id),
                                                                            ('price_unit', '=', line.price_unit)])
            else:
                iguales = False
                break
            if not product_in_compra:
                iguales = False
                break
        return iguales

    def cargar_archivo_xml(self, firmada):

        # xml_arc = etree.parse(file)
        xml_arc = firmada

        # verificar si existe la orden de compra
        num_orden_compra = xml_arc.find(".//cac:OrderReference//cbc:ID",
                                        namespaces=NSMAP_firmada).text

        id_orden_compra = False
        invoice_origin = ""
        if num_orden_compra:
            id_orden_compra = self.env["purchase.order"].search([("name", "=ilike", num_orden_compra)])
            if id_orden_compra:
                invoice_origin = id_orden_compra.name
            else:
                invoice_origin = ""

        # verificar si existe el proveedor
        IDsupplier = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:PartyTaxScheme//cbc:CompanyID",
                                  namespaces=NSMAP_firmada).text
        nombre = self.env["res.partner"].search([('vat_num', '=', IDsupplier), ('parent_id', '=', False)])
        if nombre:
            partner_id = nombre.id
        else:
            partner_id = self.env["import.xml"].CreatedSupplier(xml_arc, NSMAP_firmada).id

        ref = xml_arc.find(".//cbc:ID", namespaces=NSMAP_firmada).text
        date = xml_arc.find(".//cbc:IssueDate", namespaces=NSMAP_firmada).text
        dateDue = xml_arc.find(".//cbc:DueDate", namespaces=NSMAP_firmada).text
        type = 'in_invoice'
        state = 'draft'
        company = self.env.user.company_id
        currency = company.currency_id

        # cargar invoice_line_ids
        order_lines = []
        lineas_factura = xml_arc.findall(".//cac:InvoiceLine", namespaces=NSMAP_firmada)
        for line in lineas_factura:
            product = line.find(".//cac:Item//cbc:Description", namespaces=NSMAP_firmada)

            product_product = self.buscar_producto(product.text, IDsupplier)

            '''product_product = self.env['product.product'].search([('name', '=', product.text)])

            if not product_product:
                product_name = product.text
                #product_product = self.env["import.xml"].crearProducto(line, NSMAP_firmada)'''

            porcentajeDiscount = line.find(".//cac:AllowanceCharge//cbc:MultiplierFactorNumeric",
                                           namespaces=NSMAP_firmada)

            if porcentajeDiscount:
                porcentajeDiscount = porcentajeDiscount.text
            else:
                porcentajeDiscount = 0

            unitPriceProduct = line.find(".//cac:Price//cbc:PriceAmount", namespaces=NSMAP).text

            qty = line.find(".//cac:Price//cbc:BaseQuantity", namespaces=NSMAP).text

            # taxes
            lis_tax = []
            lis_name_tax = []
            flag_AIU = False
            for tax in line.findall(".//cac:TaxTotal//cac:TaxSubtotal", namespaces=NSMAP):
                percent_tax = tax.find(".//cac:TaxCategory//cbc:Percent",
                                       namespaces=NSMAP).text
                TaxID = tax.find(".//cac:TaxCategory//cac:TaxScheme//cbc:ID",
                                 namespaces=NSMAP).text
                tax_name = tax.find(
                    ".//cac:TaxCategory//cac:TaxScheme//cbc:Name",
                    namespaces=NSMAP).text

                if tax_name == 'AIU' and not (percent_tax == '0' or percent_tax == '0.00' or percent_tax == '0,00'):
                    flag_AIU = True
                    taxable_amount = tax.find(".//cbc:TaxAmount", namespaces=NSMAP).text
                    order_lines.append(self.env["import.xml"].createLineAIU(taxable_amount, line, NSMAP, percent_tax))

                account_tax = self.env['account.tax'].search(
                    [('type_tax_use', '=', 'purchase'), ('amount_type', '=', 'percent'),
                     ('amount', '=', percent_tax), ('type_tax.code', '=', TaxID),
                     ('name', 'like', tax_name)])

                if account_tax and not flag_AIU:
                    lis_tax.append(account_tax[0].id)
                elif not flag_AIU:
                    if tax_name:
                        tax_new = tax_name + ' ' + str(percent_tax) + '% compras'

                        if tax_new in lis_name_tax:
                            continue
                        else:
                            lis_tax.append(self.env["import.xml"].createTax(tax_name, percent_tax, TaxID))
                            lis_name_tax.append(tax_new)

            if flag_AIU:
                lis_tax = []

            data = (0, 0, {
                'price_unit': unitPriceProduct,
                'product_id': product_product['product_id'],
                'name': product_product['product_name'],
                'quantity': qty,
                'discount': porcentajeDiscount,
                'product_uom_id': product_product['product_uom_id'],
                'tax_ids': [(6, 0, lis_tax)],
            })
            order_lines.append(data)

        factura = {
            'move_type': type,
            'company_id': company.id,
            'currency_id': currency,
            'date': date,
            'state': state,
            'ref': ref,
            'invoice_date_due': dateDue,
            'invoice_date': date,
            'invoice_line_ids': order_lines,
            'partner_id': partner_id,
            'purchase_id': id_orden_compra,
            'invoice_origin': invoice_origin,
        }

        return factura
