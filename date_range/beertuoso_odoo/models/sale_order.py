from odoo import models, fields, api, _
import requests
import base64
from dateutil.relativedelta import relativedelta
from datetime import datetime
import datetime
import re


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    beertuoso_id = fields.Char(string='id beertuoso')

    def get_document_type(self, document_type):
        if document_type == 'CC':
            doc_type = self.env.ref('l10n_co.national_citizen_id').id, '13'
            return doc_type
        elif document_type == 'NIT':
            doc_type = self.env.ref('l10n_co.rut').id, '31'
            return doc_type

    def conectar_beertuso(self, url_api=None, fecha=None):
        date_now = fields.date.today().strftime('%Y%m%d') if not fecha else fecha
        api_url = "https://api-v2.cloud.smartrent.com.co/v3/odoo/rented-items?date={0}".format(
            date_now) if not url_api else url_api.format(date_now)
        response = requests.get(api_url)
        res = response.json()
        for item in res['items']:
            rental = item['rent']
            orden_existe = self.search([('beertuoso_id', '=', rental['id'])])
            if not orden_existe:
                vals = {'is_rental_order': True, }

                client = item['client']
                sponsor = item['sponsor']
                products = item['products']
                shippinginfo = item['shippingInfo']

                if 'dane' in shippinginfo:
                    city = self.env['res.city'].search([('code', '=', shippinginfo['dane'])])
                else:
                    city = self.env['res.city'].search([('name', '=ilike', shippinginfo['city'])])

                try:
                    datecreated = fields.Date.from_string(rental['datecreated'])
                    date_order = datetime.datetime.strptime(rental['datecreated'], "%Y-%m-%d")
                except:
                    datecreated = fields.Datetime.now()
                    date_order = fields.Datetime.now()

                vals['recurrent_date_invoice'] = self._get_default_date(datecreated)
                vals['date_order'] = date_order
                vals['beertuoso_id'] = rental['id']

                document_sponsor = self.GetNitCompany(str(sponsor['document']).replace(".", ""), sponsor['documentType'])
                res_sponsor = self.env['res.partner'].search([('vat_num', '=', document_sponsor[0])], limit=1)
                if not res_sponsor:
                    document_type = self.get_document_type(sponsor['documentType'])

                    vals_sponsor = {'name': sponsor['name'],
                                    'vat': '{0}-{1}'.format(document_sponsor[0], document_sponsor[1]) if sponsor[
                                                                                                             'documentType'] == 'NIT' else
                                    document_sponsor[0],
                                    'vat_num': document_sponsor[0],
                                    'vat_vd': document_sponsor[1],
                                    'company_type': 'company',
                                    'l10n_latam_identification_type_id': document_type[0] if document_sponsor[0] else False,
                                    'vat_type': document_type[1] if document_sponsor[0] else False}
                    res_sponsor = self.env['res.partner'].create(vals_sponsor)
                sponsor_id = res_sponsor.id

                documento_cliente = self.GetNitCompany(str(client['document']).replace(".", ""), client['documentType'])
                partner = self.env['res.partner'].search([('vat_num', '=', documento_cliente[0])], limit=1)
                payment_mode = self.env['account.payment.mode'].search([('name', '=ilike', rental['collect'])], limit=1)
                if not partner:
                    nombre1 = client['name'] if 'name' in client else False
                    nombre2 = client['name2'] if 'name2' in client else False
                    apellido1 = client['lastname'] if 'lastname' in client else False
                    apellido2 = client['lastname2'] if 'lastname2' in client else False
                    nombre_completo = nombre1 + ' ' + nombre2 + ' ' + apellido1 + ' ' + apellido2
                    document = self.get_document_type(client['documentType'])

                    vals_partner = {'name': nombre_completo,
                                    'firstname': nombre1,
                                    'other_name': nombre2,
                                    'lastname': apellido1,
                                    'other_lastname': apellido2,
                                    'vat': '{0}-{1}'.format(documento_cliente[0], documento_cliente[1]) if client[
                                                                                                               'documentType'] == 'NIT' else
                                    documento_cliente[0],
                                    'vat_num':  documento_cliente[0],
                                    'email': client['email'],
                                    'phone': client['phone'],
                                    'mobile': client['cellphone'],
                                    'l10n_latam_identification_type_id': document[0] if documento_cliente[0] else False,
                                    'vat_type': document[1] if documento_cliente[0] else False,
                                    'vat_vd': documento_cliente[1],
                                    'street': shippinginfo['address'],
                                    'city_id': city.id,
                                    'state_id': city.state_id.id,
                                    'country_id': city.country_id.id,
                                    'sponsor_id': sponsor_id,
                                    'customer_payment_mode_id': payment_mode.id if payment_mode else False,
                                    'xbirthday': client['birthdate'] if client['birthdate'] != "" else False}
                    partner = self.env['res.partner'].create(vals_partner)
                else:
                    vals_partner = {'street': shippinginfo['address'],
                                    'city_id': city.id,
                                    'state_id': city.state_id.id,
                                    'country_id': city.country_id.id}
                    partner.write(vals_partner)

                vals['partner_id'] = partner.id
                vals['payment_term_id'] = partner.property_payment_term_id.id if partner.property_payment_term_id else False

                order = self.create(vals)
                for product in products:
                    order_line = {}

                    producto = False
                    if 'sku' in product:
                        producto = self.env['product.product'].search([('barcode', '=', product['sku'])])

                    is_rental = False
                    if product['type'] == 'product-device':
                        is_rental = True
                    elif product['type'] == 'fee':
                        is_rental = False
                    if producto:
                        order_line['product_id'] = producto.id
                        #producto.write({'rent_ok': True})
                    else:
                        try:
                            response_image = requests.get(product['image'])
                            image = base64.b64encode(response_image.content) if 'image' in product else False
                        except:
                            image = False
                        vals_product = {'name': product['name'] if 'name' in product else False,
                                        'barcode': product['sku'] if 'sku' in product else False,
                                        'default_code': product['sku'] if 'sku' in product else False,
                                        'image_1920': image,
                                        'tracking': 'serial',
                                        'rent_ok': is_rental,
                                        'detailed_type': 'product'}
                        if 'brand' in product:
                            brand = self.env['product.brand'].search([('name', '=ilike', product['brand'])])
                            vals_product.update({'product_brand_id': brand.id if brand else self.env['product.brand'].create({'name': product['brand']})[0].id if product["brand"] != "" else False})
                        if 'specs' in product:
                            vals_product.update({'description': product['specs']})
                        if 'category' in product:
                            category = self.env['product.category'].search([('name', '=ilike', product['category'])])
                            vals_product.update({'categ_id': category.id if category else self.env['product.category'].create({'name': product['category']}).id})

                        producto = self.env['product.product'].create(vals_product)

                    order_line['product_id'] = producto.id

                    if 'serial' in product and 'deliverydate' in product:
                        pickedup_lot_id = self.env['stock.production.lot'].search([('name', '=', product['serial']),
                                                                                   ('product_id', '=', producto.id),
                                                                                   ('company_id', '=', self.env.company.id)])
                        if pickedup_lot_id:
                            lot_id = pickedup_lot_id
                        else:
                            lot_id = self.env['stock.production.lot'].create({'name': product['serial'],
                                                                              'product_id': producto.id,
                                                                              'company_id': self.env.company.id})
                        order_line['pickedup_lot_ids'] = [(6, 0, [lot_id.id])]
                        order_line['qty_delivered'] = 1

                        pickup_date = datetime.datetime.strptime(product['deliverydate'], "%Y-%m-%d")
                    else:
                        pickup_date = fields.Date.from_string(rental['datecreated'])

                    rental_value = product['canonSelected']

                    months = rental_value['months'] if rental_value['months'] is not None else 1
                    value = rental_value['value'] if rental_value['value'] is not None else 0
                    retake = rental_value['retake'] if rental_value['retake'] is not None else 0

                    order_line['product_uom_qty'] = 1
                    order_line['order_id'] = order.id
                    order_line['pickup_date'] = pickup_date
                    order_line['return_date'] = pickup_date + relativedelta(
                        months=months)
                    order_line['price_month'] = float(value)
                    order_line['valor_retoma'] = retake
                    order_line['price_unit'] = float(value) * float(months)
                    order_line['months_rental'] = months
                    order_line['is_rental'] = is_rental
                    self.env['sale.order.line'].create(order_line)
                if order:
                    order.action_confirm()
                    order.write({'recurrent_date_invoice': self._get_default_date(datecreated),
                                'date_order':date_order})
        return res

    def GetNitCompany(self, number, doc_type):
        document = ''
        dv = ''
        try:
            if not re.match("^[0-9]+$", number) is None:
                if '-' in number:
                    document = number[0:number.find('-')]
                    dv = number[-1]
                else:
                    document = number
                    dv = str(self._compute_vat_vd(number)) if doc_type == 'NIT' else ''
                return document, dv
            else:
                return False, False
        except:
            return document, dv

    def _compute_vat_vd(self, vat_num):
        factor = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
        factor = factor[-len(vat_num):]
        csum = sum([int(vat_num[i]) * factor[i] for i in range(len(vat_num))])
        check = csum % 11
        if check > 1:
            check = 11 - check
        return check

    def _get_default_date(self, date):
        # date_now = datetime.now()
        invoice_date = date + relativedelta(months=1)
        month = invoice_date.month
        year = invoice_date.year
        real_invoice_date = str(datetime.date(year, month, 1))
        return real_invoice_date


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    valor_retoma = fields.Float(string='Valor retoma')
