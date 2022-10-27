from dateutil.relativedelta import relativedelta
from datetime import datetime
import datetime
import base64
import calendar
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
import base64
import os
import pandas as pd

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    future_flow_line_ids = fields.One2many('future.flow.line', 'sale_rental_schedule_id', string='Flujo futuro')
    price_month = fields.Float(string='Precio Mensual')
    months_rental = fields.Float(string='Meses')
    percent_invoice = fields.Float(string='Porcentaje de facturacion')
    lot_recogida_id = fields.Many2one('stock.production.lot', string='Lote/Nro Serie', readonly=True,
                                      compute='_get_lot_recogida')

    @api.depends('pickedup_lot_ids')
    def _get_lot_recogida(self):
        for rec in self:
            if rec.is_rental:
                rec.lot_recogida_id = rec.pickedup_lot_ids.ids[0] if rec.pickedup_lot_ids else False
            else:
                rec.lot_recogida_id = False


    @api.onchange('product_id')
    def _get_domain(self):
        lot_id = self.env['stock.production.lot'].search(
            [('product_id', '=', self.product_id.id)])
        lot = lot_id.filtered(lambda lot: lot.product_qty >= 0)
        return {'domain': {'lot_recogida_id': [('id', 'in', lot.ids)]}}

    @api.onchange('price_month', 'months_rental')
    def product_price_month_change(self):
        self.price_unit = self.price_month * self.months_rental

    @api.onchange('price_unit')
    def price_unit_change(self):
        if self.is_rental:
            try:
                self.price_month = self.price_unit/self.months_rental
            except ZeroDivisionError:
                self.price_month = 0

    @api.onchange('pickup_date', 'return_date')
    def pickup_return_date(self):
        if self.is_rental:
            duration_month = self._compute_duration(self.pickup_date, self.return_date)
            self.months_rental = duration_month['month']

    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        for line in res:
            if line.is_rental:
                line.create_flujo()
        return res

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        if 'pickup_date' in vals or 'return_date' in vals:
            self.create_flujo()
        return res

    def get_sale_order_line_multiline_description_sale(self, product):
        res = super(SaleOrderLine, self).get_sale_order_line_multiline_description_sale(product)
        if self.is_rental:
            res = "Alquiler de equipo tecnológico - " + res
        return res

    def create_flujo(self):
        self.ensure_one()
        # res_id = self.env['sale.rental.schedule'].search([('order_line_id', '=', self.id)])
        duration = self._compute_duration(self.pickup_date, self.return_date)
        future_flow_line = []
        future_ids = []

        #invoice_date = self.pickup_date + relativedelta(months=1)
        if self.order_id.invoice_pickup:
            invoice_date = self.pickup_date + relativedelta(months=1)
            month = invoice_date.month
            year = invoice_date.year
            day = self.pickup_date.day
            installment_date = datetime.datetime(year, month, day)
            real_invoice_date = datetime.datetime(year, month, day)
        elif self.order_id.recurrent_date_invoice == self.pickup_date.date():
            invoice_date = self.pickup_date + relativedelta(months=1)
            month = invoice_date.month
            year = invoice_date.year
            day = self.order_id.recurrent_date_invoice.day
            installment_date = datetime.datetime(year, month, day)
            #installment_date = invoice_date
            real_invoice_date = datetime.datetime(year, month, day)
            #real_invoice_date = invoice_date
        else:
            invoice_date = datetime.datetime.strptime(fields.Datetime.to_string(self.order_id.recurrent_date_invoice), '%Y-%m-%d %H:%M:%S')
            # installment_date = datetime.datetime(year, month, 1)
            installment_date = invoice_date
            # real_invoice_date = datetime.datetime(year, month, 1)
            real_invoice_date = invoice_date




        old_installment_date = self.pickup_date

        if real_invoice_date < old_installment_date:
            real_invoice_date = real_invoice_date + relativedelta(months=1)
            installment_date = real_invoice_date

        total_price = 0
        for i in range(duration['month']):
            if installment_date <= self.return_date:
                this_installment = i + 1
                duration_month = self._compute_duration(old_installment_date, installment_date)
                month_range = calendar.monthrange(old_installment_date.year, old_installment_date.month)
                '''unit_price_month = self.env['rental.pricing'].search(
                    [('product_template_id', '=', self.product_id.product_tmpl_id.id),
                     ('unit', '=', 'month')])._compute_price(1, 'month')'''
                unit_price_month = self.price_month
                days = duration_month['day'] - 1 if installment_date == self.return_date else duration_month['day']
                unit_price = self.price_unit - total_price if installment_date == self.return_date else days * unit_price_month / month_range[1]
                total_price += unit_price
                try:
                    percent_invoice = unit_price*1/self.price_unit
                except ZeroDivisionError:
                    percent_invoice = 0

                vals = {
                    "product_id": self.product_id.id,
                    "invoice_date_ini": old_installment_date,
                    "invoice_date_fin": installment_date if installment_date == self.return_date else installment_date - relativedelta(
                        days=1),
                    "invoice_date": real_invoice_date if not self.order_id.invoice_pickup else real_invoice_date - relativedelta(months=1),
                    "sale_rental_schedule_id": self.id,
                    'amount_payment': unit_price,
                    'percent_invoice': percent_invoice,
                }
                future_id = self.env['future.flow.line'].create(vals)
                future_ids.append(future_id.id)
                old_installment_date = installment_date
                installment_date = self._next_date(
                    installment_date, 1, "month"
                )
                if this_installment > 1:
                    real_invoice_date = self._next_date(
                        real_invoice_date, 1, "month"
                    )
                if installment_date.month == self.return_date.month and installment_date.year == self.return_date.year:
                    installment_date = self.return_date
        future_flow_line.append((6, 0, future_ids))
        return self.write({"future_flow_line_ids": future_flow_line,
                           "percent_invoice": duration['month']})

    def action_show_flujo(self):
        if self.is_rental:
            self.create_flujo()
        view = self.env.ref('alquiler_flujo_futuro.view_flujo_futuro')
        action = {
            'name': _('Flujo futuro'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'flags': {'form': {'action_buttons': False}}
        }
        return action

    def open_cambio(self):
        status = "cambio"
        lines_to_return = self.id
        return self._open_rental_wizard(status, lines_to_return)

    def _open_rental_wizard(self, status, order_line_ids):
        context = {
            'order_line_ids': order_line_ids,
            'default_status': status,
            'default_order_id': self.order_id.id,
        }
        if status == 'pickup':
            name = _('Validate a pickup')
        elif status == 'return':
            name = _('Validate a return')
        else:
            name = _('Cambio de serial')
        return {
            'name': name,
            'view_mode': 'form',
            'res_model': 'rental.order.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

    def _compute_duration(self, pickup_date, return_date):
        duration_dict = self.env['rental.pricing']._compute_duration_vals(pickup_date, return_date)
        return duration_dict

    @api.model
    def _next_date(self, installment_date, interval, interval_type):
        installment_date = fields.Date.from_string(installment_date)
        if interval_type == "month":
            next_date = installment_date + relativedelta(months=+interval)
        elif interval_type == "year":
            next_date = installment_date + relativedelta(years=+interval)
        else:
            next_date = installment_date + relativedelta(days=+interval)
        next_date = datetime.datetime.strptime(fields.Datetime.to_string(next_date), '%Y-%m-%d %H:%M:%S')
        return next_date



class FutureFlowLine(models.Model):
    _name = 'future.flow.line'
    _description = 'lineas de flujo futuro'

    product_id = fields.Many2one('product.product', string='Producto', related='sale_rental_schedule_id.product_id', store=True)
    invoice_date_ini = fields.Date(string='Fecha inicio')
    invoice_date_fin = fields.Date(string='Fecha fin')
    invoice_date = fields.Date(string='Fecha factura')
    amount_payment = fields.Float(string='Valor a pagar')
    sale_rental_schedule_id = fields.Many2one('sale.order.line', string='Horario alquiler')
    percent_invoice = fields.Float(string='Porcentaje factura', digits='Product Unit of Measure')
    sale_order = fields.Char(string='orden', related='sale_rental_schedule_id.order_id.name', store=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', related='sale_rental_schedule_id.order_id.partner_id', store=True)
    lot_id = fields.Many2one('stock.production.lot', string='Nro Serie', related='sale_rental_schedule_id.lot_recogida_id', store=True)
    #sequence = fields.Integer(string='')

    '''@api.depends('sale_rental_schedule_id')
    def _get_id_lots(self):
        for rec in self:
            if rec.sale_rental_schedule_id.is_rental:
                rec.lot_id = rec.sale_rental_schedule_id.pickedup_lot_ids.ids[0] if rec.sale_rental_schedule_id else False'''


class RentalWizard(models.TransientModel):
    _inherit = 'rental.wizard'

    amount_month = fields.Float(string='Precio de renta')
    months = fields.Integer(string='Meses')

    @api.onchange('pickup_date', 'return_date')
    def _compute_dates_pick_return(self):
        for wizard in self:
            duration_dict = self.env['rental.pricing']._compute_duration_vals(wizard.pickup_date, wizard.return_date)
            wizard.months = duration_dict['month']

    @api.onchange('months')
    def _compute_dates_months(self):
        for wizard in self:
            if wizard.months > 0:
                return_date = wizard.pickup_date + relativedelta(months=wizard.months)
                wizard.return_date = return_date


    @api.onchange('unit_price', 'duration')
    def amount_month_change(self):
        for wizard  in self:
            try:
                wizard.amount_month = wizard.unit_price / wizard.duration
            except ZeroDivisionError:
                wizard.amount_month = 0

    @api.onchange('amount_month')
    def price_unit_onchange(self):
        for wizard in self:
            wizard.unit_price = wizard.amount_month * wizard.duration


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_default_date_invoice(self):
        #date_now = datetime.now()
        invoice_date = datetime.datetime.now() + relativedelta(months=1)
        month = invoice_date.month
        year = invoice_date.year
        real_invoice_date = datetime.datetime(year, month, 1)
        return real_invoice_date

    recurrent_date_invoice = fields.Date(string='Fecha de facturacion', default=_get_default_date_invoice)
    invoice_pickup = fields.Boolean(string='Facturar al recoger', help='El día en que se haga la facturación sera tomado de la fecha de recogida del producto')

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if self.is_rental_order:
            for line in self.order_line:
                if ('recurrent_date_invoice' in vals or 'invoice_pickup' in vals) and self.state == 'draft':
                    line.create_flujo()
                if line.product_uom_qty > 1 and line.is_rental and line.is_product_rentable:
                    cantidad = int(line.product_uom_qty - 1)
                    for i in range(cantidad):
                        new_line = line.copy({'order_id': self.id,
                                              'pickup_date': line.pickup_date,
                                              'return_date': line.return_date,
                                              'product_uom_qty': 1,
                                              'months_rental': line.months_rental,})
                    line.write({'product_uom_qty': 1})
        return res

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res.is_rental_order:
            for line in res.order_line:
                if line.product_uom_qty > 1 and line.is_rental and line.is_product_rentable:
                    cantidad = int(line.product_uom_qty - 1)
                    for i in range(cantidad):
                        new_line = line.copy({'order_id': res.id,
                                              'pickup_date': line.pickup_date,
                                              'return_date': line.return_date,
                                              'product_uom_qty': 1,
                                              'months_rental': line.months_rental,})
                    line.write({'product_uom_qty': 1})
        return res


class RentalProcessing(models.TransientModel):
    _inherit = 'rental.order.wizard'

    file_import = fields.Binary("Importar Archivo 'xlxs'",
                                help="*Importar un lista de numeros de serie de un archivo de excel \n *Solo archivos .xlsx"
                                     "\n *El archivo debe contener una columna 'PRODUCTO' y una 'SERIE'")
    file_name = fields.Char("Nombre del archivo")

    file_xlsx = fields.Binary(string="Archivo")
    status = fields.Selection(selection_add=[('cambio', 'Cambio')])

    def cargar_archivo(self):
        if self.file_import:
            file_value = self.file_import.decode("utf-8")
            filename, FileExtension = os.path.splitext(self.file_name)
            if FileExtension != '.xlsx':
                raise UserError("Archivo invalido! Por favor agregar un archiv 'xlsx'")
            f = base64.decodestring(self.file_import)
            dataframe2 = pd.read_excel(f, sheet_name=None, names=['PRODUCTO', 'SERIE'])
            vals = []
            for key in dataframe2:
                for index in dataframe2[key].index:
                    vals.append({'product': dataframe2[key]['PRODUCTO'][index],
                                 'serie': dataframe2[key]['SERIE'][index]})

            for val in vals:
                line = self.env['rental.order.wizard.line'].search([('rental_order_wizard_id', '=', self.id),
                                                                    ('product_id.default_code', '=', val['product']),
                                                                    ('pickedup_lot_ids', '=', False),
                                                                    ('tracking', '=', 'serial')], limit=1)
                pickedup_lot_id = self.env['stock.production.lot'].search([('name', '=', val['serie']),
                                                                           ('product_id', '=', line.product_id.id)])
                list = [(6, 0, [pickedup_lot_id.id])]
                line.write({'pickedup_lot_ids': list, 'qty_delivered': 1 })
                #line.order_line_id.write({'pickedup_lot_ids': list})

    def apply(self):
        for wizard in self:
            wizard.cargar_archivo()
        res = super(RentalProcessing, self).apply()
        return res


    def cargar_archivo2(self):
        file_xlsx = self.file_xlsx
        if file_xlsx:
            f = base64.decodestring(self.file_xlsx)
            dataframe2 = pd.read_excel(f, sheet_name=None, names=['PRODUCTO', 'SERIE'])
            vals = []
            for key in dataframe2:
                for index in dataframe2[key].index:
                    vals.append({'product': dataframe2[key]['PRODUCTO'][index],
                                 'serie': dataframe2[key]['SERIE'][index]})

            for val in vals:
                line = self.env['rental.order.wizard.line'].search([('rental_order_wizard_id', '=', self.id),
                                                                    ('product_id.default_code', '=', val['product']),
                                                                    ('pickedup_lot_ids', '=', False),
                                                                    ('tracking', '=', 'serial')], limit=1)
                pickedup_lot_id = self.env['stock.production.lot'].search([('name', '=', val['serie'])])
                list = [(6, 0, [pickedup_lot_id.id])]
                line.write({'pickedup_lot_ids': list})
        return {"type": "ir.actions.act_window"}

class RentalProcessingLine(models.TransientModel):
    _inherit = 'rental.order.wizard.line'

    pickup_date = fields.Datetime(string='Fecha recogida', default=fields.Datetime.now())
    return_date = fields.Datetime(string='Fecha devolución', default=fields.Datetime.now())
    serial_anterior = fields.Many2one('stock.production.lot', domain="[('product_id','=',product_id)]",)
    nuevo_serial = fields.Many2one('stock.production.lot',
                                   domain="[('product_id','=',product_id),('id','in',pickeable_lot_ids)]")
    fecha_cambio = fields.Datetime(string='Fecha cambio', default=fields.Datetime.now())

    def _default_wizard_line_vals(self, line, status):
        if status == "cambio":
            status = "pickup"
            res = super(RentalProcessingLine, self)._default_wizard_line_vals(line, status)
            returned_lots = line.returned_lot_ids
            pickedup_lots = line.pickedup_lot_ids
            returnable_lots = pickedup_lots - returned_lots
            res.update({'serial_anterior': returnable_lots.id})
        else:
            res = super(RentalProcessingLine, self)._default_wizard_line_vals(line, status)

        return res

    def _apply(self):
        res = super(RentalProcessingLine, self)._apply()
        for wizard_line in self:
            order_line = wizard_line.order_line_id
            if wizard_line.status == 'pickup' and wizard_line.qty_delivered > 0:
                order_line.pickup_date = wizard_line.pickup_date
                order_line.return_date = wizard_line.calcular_devolucion(order_line.months_rental)
            elif wizard_line.status == 'return' and wizard_line.qty_returned > 0:
                order_line.return_date = wizard_line.return_date
            elif wizard_line.status == 'cambio':
                if wizard_line.nuevo_serial:
                    cambio_lot_ids = wizard_line.nuevo_serial
                    lot_anterior = wizard_line.order_line_id.pickedup_lot_ids[0]
                    location_dest_id = self.env['stock.location'].search([('name', '=', 'Stock')]).id
                    location_id = self.env['stock.location'].search([('name', '=', 'Rental')]).id
                    product_id = wizard_line.order_line_id.product_id

                    stock_move = {
                        'name': 'Cambio de producto de renta',
                        'date': wizard_line.fecha_cambio,
                        'company_id': self.env.company.id,
                        'product_id': product_id.id,
                        'lot_ids': [(4, lot_anterior.id)],
                        'location_id': location_id,
                        'location_dest_id': location_dest_id,
                        'product_uom_qty': 1,
                        'product_uom': product_id.uom_id.id,
                    }
                    stock_picking = self.env['stock.picking'].create({'origin': wizard_line.order_line_id.name,
                                                                      'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1).id,
                                                                      'location_dest_id': location_dest_id,
                                                                      'location_id': location_id,
                                                                      'company_id': self.env.company.id, 'move_ids_without_package': [(0, 0, stock_move)]})
                    stock_picking.action_confirm()
                    stock_picking.button_validate()
                    order_line.write({
                        'pickedup_lot_ids': [(6, 0, cambio_lot_ids.ids)],
                    })
                else:
                    raise ValidationError(_('Debe elegir un nuevo serial'))
            order_line.create_flujo()
        return res

    def calcular_devolucion(self, meses):
        return fields.Datetime.now() + relativedelta(months=meses)
