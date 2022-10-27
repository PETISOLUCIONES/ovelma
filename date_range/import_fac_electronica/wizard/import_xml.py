from odoo import api, fields, models, _
from lxml import etree
import base64
from odoo.exceptions import UserError


class ImportXML(models.TransientModel):
    _name = "import.xml"
    _description = "Importar facturas xml"

    arc = fields.Binary(string="Archivo")
    nomArc = fields.Char(string="Nombre del archivo")

    def cargar_archivo(self):
        arc = self.arc
        if arc:
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
            f = base64.decodestring(self.arc)
            xml_arc = etree.fromstring(f)

            # verificar si existe la orden de compra
            namePO = xml_arc.find(".//cac:OrderReference//cbc:ID",
                                  namespaces=NSMAP)

            idOP = None
            invoice_origin = None
            if not namePO.text is None:
                idOP = self.env["purchase.order"].search([
                    ("name", "=", namePO.text)
                ])
                if idOP:
                    invoice_origin = idOP.name
                else:
                    idOP = None

            # verificar si existe el proveedor
            IDsupplier = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:PartyLegalEntity//cbc:CompanyID", namespaces=NSMAP).text
            nombre = self.env["res.partner"].search([('vat_num', '=', IDsupplier)])
            if nombre:
                partner_id = nombre.id
            else:
                partner_id = self.CreatedSupplier(xml_arc, NSMAP).id

            ref = xml_arc.find(".//cbc:ID", namespaces=NSMAP).text
            date = xml_arc.find(".//cbc:IssueDate", namespaces=NSMAP).text
            dateDue = xml_arc.find(".//cbc:DueDate", namespaces=NSMAP).text
            move_type = 'in_invoice'
            state = 'draft'
            company = self.env.user.company_id
            currency = company.currency_id

            #cargar invoice_line_ids
            order_lines = []
            for line in xml_arc.findall(".//cac:InvoiceLine", namespaces=NSMAP):
                product = line.find(".//cac:Item//cbc:Description", namespaces=NSMAP)
                product_product = self.env['product.product'].search([('name', '=', product.text)])

                if not product_product:
                    product_product = self.crearProducto(line, NSMAP)

                porcentajeDiscount = line.find(".//cac:AllowanceCharge//cbc:MultiplierFactorNumeric",
                                               namespaces=NSMAP)

                if porcentajeDiscount:
                    porcentajeDiscount.text
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
                        order_lines.append(self.createLineAIU(taxable_amount, line, NSMAP, percent_tax))

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
                    'product_id': product_product.id,
                    'quantity': qty,
                    'discount': porcentajeDiscount,
                    'product_uom_id': product_product.uom_id,
                    'tax_ids': [(6, 0, lis_tax)],
                })
                order_lines.append(data)

            factura = self.env['account.move'].create({
                'move_type': move_type,
                'company_id': company.id,
                'currency_id': currency,
                'date': date,
                'state': state,
                'ref': ref,
                'invoice_date_due': dateDue,
                'invoice_date': date,
                'invoice_line_ids': order_lines,
                'partner_id': partner_id,
                'purchase_id': idOP,
                'invoice_origin': invoice_origin,
            })

            if factura["purchase_id"]:
                ls_invoices = self.env["purchase.order"].search(
                    [('id', '=', factura["purchase_id"].id)]).invoice_ids.ids

                purchase_order = self.env["purchase.order"].search(
                    [('id', '=', factura["purchase_id"].id)]).write({'invoice_ids': [(4, factura.id)],
                                                                     'invoice_count': len(
                                                                         ls_invoices) + 1,
                                                                     'invoice_status': 'invoiced'})

            factura.action_post()
        else:
            raise UserError("Debe elegir un archivo")

        return {'name': 'Factura Importada',
                'res_model': 'account.move',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': factura.id,
                'view_id': self.env.ref('account.view_move_form').id,
                'context': self.env.context,
                'target': 'current',
                'type': 'ir.actions.act_window'}

    def TypeDocumentCust(self, schemeName):
        type = ''
        if schemeName == '31':
            type = 'rut'
        elif schemeName == '13':
            type = 'id_document'
        elif schemeName == '12':
            type = 'id_card'
        elif schemeName == '41':
            type = 'passport'
        elif schemeName == '22':
            type = 'foreign_id_card'
        elif schemeName == '50':
            type = 'external_id'
        elif schemeName == '':
            type = 'diplomatic_card'
        elif schemeName == '':
            type = 'residence_document'
        elif schemeName == '11':
            type = 'civil_registration'
        elif schemeName == '13':
            type = 'national_citizen_id'
        elif schemeName == '91':
            type = 'niup_id'
        return type

    def TypeUom(self, uom):
        type = self.env['uom.uom'].search([('name', '=', uom)])
        if not type:
            category = self.env['uom.category'].search([('name', '=', 'Otro')])
            if not category:
                category = self.env['uom.category'].create({'name': 'Otro'})

            type = self.env['uom.uom'].create({
                'name': uom,
                'category_id': category.id
            })

        return type

    def CreatedSupplier(self, xml_arc, NSMAP):
        nameSupplier = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:PartyName//cbc:Name",
                                    namespaces=NSMAP).text
        country_code = xml_arc.find(
            ".//cac:AccountingSupplierParty//cac:Party//cac:PhysicalLocation//cac:Address//cac:Country//cbc:IdentificationCode",
            namespaces=NSMAP).text
        city = xml_arc.find(
            ".//cac:AccountingSupplierParty//cac:Party//cac:PhysicalLocation//cac:Address//cbc:CityName",
            namespaces=NSMAP).text
        city_id = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:PhysicalLocation//cac:Address//cbc:ID",
                               namespaces=NSMAP).text
        department = xml_arc.find(
            ".//cac:AccountingSupplierParty//cac:Party//cac:PhysicalLocation//cac:Address//cbc:CountrySubentity",
            namespaces=NSMAP).text
        state_id = xml_arc.find(
            ".//cac:AccountingSupplierParty//cac:Party//cac:PhysicalLocation//cac:Address//cbc:CountrySubentityCode",
            namespaces=NSMAP).text
        street = xml_arc.find(
            ".//cac:AccountingSupplierParty//cac:Party//cac:PhysicalLocation//cac:Address//cac:AddressLine//cbc:Line",
            namespaces=NSMAP).text
        shcemeName = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:PartyTaxScheme//cbc:CompanyID",
                                  namespaces=NSMAP).attrib['schemeName']
        type_document = self.TypeDocumentCust(shcemeName)
        vat_num = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:PartyLegalEntity//cbc:CompanyID",
                               namespaces=NSMAP).text
        vat_vd = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:PartyLegalEntity//cbc:CompanyID",
                              namespaces=NSMAP).attrib['schemeID']
        tel_supplier = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:Contact//cbc:Telephone",
                                    namespaces=NSMAP).text
        email_supplier = xml_arc.find(".//cac:AccountingSupplierParty//cac:Party//cac:Contact//cbc:ElectronicMail",
                                      namespaces=NSMAP).text

        email_supplier = email_supplier.split(';')

        organization_type_id = xml_arc.find(".//cac:AccountingSupplierParty//cbc:AdditionalAccountID",
                                            namespaces=NSMAP).text
        fiscal_responsibilities = xml_arc.find(
            ".//cac:AccountingSupplierParty//cac:Party//cac:PartyTaxScheme//cbc:TaxLevelCode", namespaces=NSMAP).text
        fiscal_responsibility_names = fiscal_responsibilities.split(';')
        ids = []
        for respon in fiscal_responsibility_names:
            ids.append((self.env['dian.fiscalresponsibility'].search(
                [('name', '=', respon)])).id)

        fiscal_responsibility_partner_ids = [(6, 0, ids)]
        resPartner = self.env['res.partner'].create({
            'company_type': 'company',
            'name': nameSupplier,
            'country_id': self.env['res.country'].search([('code', '=', country_code)]).id,
            'city_id': self.env['res.city'].search([('code', '=', city_id)]).id,
            'city': self.env['res.city'].search([('code', '=', city_id)]).name,
            'state_id': self.env['res.country.state'].search([('dian_state_code', '=', state_id)]).id,
            'street': street,
            'l10n_latam_identification_type_id': self.env["l10n_latam.identification.type"].search(
                [('l10n_co_document_code', '=', 'rut')], limit=1).id,
            'vat_num': vat_num,
            'vat_vd': vat_vd,
            'phone': tel_supplier,
            'email': email_supplier[0],
            'organization_type_id': organization_type_id,
            'fiscal_responsibility_partner_ids': fiscal_responsibility_partner_ids,
            'supplier_rank': 1,

        })

        return resPartner

    def crearProducto(self, line, NSMAP):
        name = line.find('.//cac:Item//cbc:Description', namespaces=NSMAP).text

        vals = {
            'name': name,
                }

        product = self.env['product.template'].create(vals)
        product_product = self.env['product.product'].search([('product_tmpl_id', '=', product.id)])

        return product_product


    def createTax(self, tax_name, percent_tax, TaxID):
        return self.env['account.tax'].create({
                            'name': tax_name + ' ' + str(percent_tax) + ' compras',
                            'type_tax_use': 'purchase',
                            'amount_type': 'percent',
                            'amount': percent_tax,
                            'type_tax': self.env['dian.typetax'].search([('code', '=', TaxID)]).id
                        }).id


    def createLineAIU(self, price, line, NSMAP, percent_tax):
        nameLine = 'AIU ' + percent_tax + '%'
        aiu = self.env["product.product"].search([('name', '=', nameLine)])
        lis_tax = []
        if not aiu:
           vals = {'name': nameLine}
           aiu_create = self.env['product.template'].create(vals)
           aiu = self.env['product.product'].search([('product_tmpl_id', '=', aiu_create.id)])

        for tax in line.findall(".//cac:TaxTotal//cac:TaxSubtotal", namespaces=NSMAP):
            percent_tax = tax.find(".//cac:TaxCategory//cbc:Percent",
                                   namespaces=NSMAP).text
            TaxID = tax.find(".//cac:TaxCategory//cac:TaxScheme//cbc:ID",
                             namespaces=NSMAP).text
            tax_name = tax.find(
                ".//cac:TaxCategory//cac:TaxScheme//cbc:Name",
                namespaces=NSMAP).text

            account_tax = self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase'), ('amount_type', '=', 'percent'),
                 ('amount', '=', percent_tax), ('type_tax.code', '=', TaxID),
                 ('name', 'like', tax_name)])

            if account_tax and tax_name == "IVA":
                lis_tax.append(account_tax[0].id)

        return (0, 0, {
            'price_unit': price,
            'product_id': aiu.id,
            'quantity': 1,
            'discount': 0,
            'product_uom_id': aiu.uom_id,
            'tax_ids': [(6, 0, lis_tax)],
        })
