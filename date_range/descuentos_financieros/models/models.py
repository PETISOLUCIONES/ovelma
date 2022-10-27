# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    financial_discount = fields.Float(string="Descuento financiero", readonly=True, default=0)

    @api.onchange('payment_date')
    def onchange_payment_date(self):
        porcentaje = self._get_porcentaje_descuento()
        facturas = self.env['account.move'].search([('id', 'in', self.env.context['active_ids'])])
        if porcentaje != 0:
            porcentaje_descuento = (100 - porcentaje) / 100
            self.financial_discount = (facturas.amount_untaxed * porcentaje_descuento)
            self.amount = facturas.amount_total
        else:
            self.financial_discount = 0
            #self.amount = facturas.amount_total

    def _get_porcentaje_descuento(self):
        if self.partner_id.property_supplier_payment_term_id:
            facturas = self.env['account.move'].search([('id', 'in', self.env.context['active_ids'])])
            if len(facturas) == 1:
                plazos = self.partner_id.property_supplier_payment_term_id.line_ids
                fecha_factura = facturas.invoice_date
                fecha_pago = self.payment_date
                days = (fecha_pago - fecha_factura).days
                list_days = []
                for plazo in plazos:
                    if plazo.value == 'percent':
                        list_days.append(plazo.days)
                list_days.sort()
                dias = None
                porcentaje = 0
                for x in range(0, len(list_days)):
                    if x == 0:
                        if fecha_pago >= fecha_factura and fecha_pago <= fecha_factura +timedelta(days=list_days[x]):
                            dias = list_days[x]
                    else:
                        if fecha_pago > fecha_factura + timedelta(days=list_days[x-1]) and fecha_pago <= fecha_factura + timedelta(days=list_days[x]):
                            dias = list_days[x]

                for plazo in plazos:
                    if plazo.value == 'percent':
                        if plazo.days == dias:
                            porcentaje = plazo.value_amount

                return porcentaje
            else:
                return 0
        else:
            return 0

    def apply_discount(self):
        porcentaje = self._get_porcentaje_descuento()
        facturas = self.env['account.move'].search([('id', 'in', self.env.context['active_ids'])])
        if porcentaje != 0:
            self.financial_discount = facturas.amount_untaxed - (facturas.amount_untaxed * porcentaje / 100)
            self.amount = facturas.amount_total - (facturas.amount_untaxed - (facturas.amount_untaxed * porcentaje / 100))
        else:
            self.financial_discount = 0
            self.amount = facturas.amount_total
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment.register',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    financial_discount = fields.Float(string="Descuento financiero", readonly=True, default=0 )


    @api.onchange('date')
    def onchange_payment_date(self):
        porcentaje = self._get_porcentaje_descuento()
        if porcentaje != 0:
           porcentaje_descuento = (100 - porcentaje) / 100
           self.financial_discount = (self.invoice_ids.amount_untaxed * porcentaje_descuento)
           self.amount = self.invoice_ids.amount_total
        else:
            self.financial_discount = 0
            self.amount = self.invoice_ids.amount_total



    def _get_porcentaje_descuento(self):
        if self.partner_id.property_supplier_payment_term_id:
            plazos = self.partner_id.property_supplier_payment_term_id.line_ids
            fecha_factura = self.invoice_ids.invoice_date
            fecha_pago = self.date
            days = (fecha_pago - fecha_factura).days
            list_days = []
            for plazo in plazos:
                if plazo.value == 'percent':
                    list_days.append(plazo.days)
            list_days.sort()
            dias = None
            porcentaje = 0
            for x in range(0, len(list_days)):
                if x == 0:
                    if fecha_pago >= fecha_factura and fecha_pago <= fecha_factura +timedelta(days=list_days[x]):
                        dias = list_days[x]
                else:
                    if fecha_pago > fecha_factura + timedelta(days=list_days[x-1]) and fecha_pago <= fecha_factura + timedelta(days=list_days[x]):
                        dias = list_days[x]

            for plazo in plazos:
                if plazo.value == 'percent':
                    if plazo.days == dias:
                        porcentaje = plazo.value_amount

            return porcentaje
        else:
            return 0

    def apply_discount(self):
        porcentaje = self._get_porcentaje_descuento()
        if porcentaje != 0:
            self.financial_discount = self.invoice_ids.amount_untaxed - (self.invoice_ids.amount_untaxed * porcentaje / 100)
            self.amount = self.invoice_ids.amount_total - (self.invoice_ids.amount_untaxed - (self.invoice_ids.amount_untaxed * porcentaje / 100))
        else:
            self.financial_discount = 0
            self.amount = self.invoice_ids.amount_total
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class AccountMove(models.Model):
    _inherit = 'account.move'

    financial_discount = fields.Monetary(string='Descuento financiero', store=False, compute='_compute_financial_discount', search='_search_financial_discount')
    date_financial_discount = fields.Date(string='Fecha limite descuento financiero', compute='_date_financial_discount', store=False, help='Fecha limite para realizar el pago y tener descuento financiero')
    porc_financial_discount = fields.Float(string='% descuento financiero', compute='_porc_financial_discount')

    def _search_financial_discount(self, operator, value):
        moves = self.env['account.move'].search([('move_type', 'in', ['in_invoice', 'out_invoice'])], limit=None)
        data = []
        for move in moves:
            if move.financial_discount > value:
                data.append(move.id)
        return [('id', 'in', data)]

    @api.depends('partner_id', 'invoice_date', 'amount_untaxed', 'payment_state', 'porc_financial_discount')
    def _porc_financial_discount(self):
        for move in self:
            if move.partner_id and move.payment_state != 'paid':
                if move.partner_id.property_supplier_payment_term_id:
                     move.porc_financial_discount = 100 - move._get_porcentaje_descuento()
                else:
                    move.porc_financial_discount = 0
            else:
                move.porc_financial_discount = 0


    @api.depends('partner_id', 'invoice_date', 'amount_untaxed', 'payment_state',  'porc_financial_discount')
    def _date_financial_discount(self):
        for move in self:
            if move.partner_id and move.payment_state != 'paid':
                if move.partner_id.property_supplier_payment_term_id:
                    days = move._get_days_discount()
                    if days != None:
                        fecha_factura = move.invoice_date
                        if fecha_factura:
                            delta = timedelta(days=days)
                            fecha_limite = fecha_factura + delta
                            move.date_financial_discount = fecha_limite
                        else:
                            move.date_financial_discount = None
                    else:
                        move.date_financial_discount = None
                else:
                    move.date_financial_discount = None
            else:
                move.date_financial_discount = None
        return {
            'context': self.env.context
        }

    def _get_porcentaje_descuento(self):
        if self.partner_id.property_supplier_payment_term_id:
            plazos = self.partner_id.property_supplier_payment_term_id.line_ids
            fecha_factura = self.invoice_date
            if fecha_factura:
                fecha_actual = datetime.now().date()
                days = (fecha_actual - fecha_factura).days
                list_days = []
                for plazo in plazos:
                    if plazo.value == 'percent':
                        list_days.append(plazo.days)
                list_days.sort()
                dias = None
                porcentaje = 0
                for x in range(0, len(list_days)):
                    if x == 0:
                        if fecha_actual >= fecha_factura and fecha_actual <= fecha_factura +timedelta(days=list_days[x]):
                            dias = list_days[x]
                    else:
                        if fecha_actual > fecha_factura + timedelta(days=list_days[x-1]) and fecha_actual <= fecha_factura + timedelta(days=list_days[x]):
                            dias = list_days[x]

                for plazo in plazos:
                    if plazo.value == 'percent':
                        if dias != None:
                            if plazo.days == dias:
                                porcentaje = plazo.value_amount
                        else:
                            porcentaje= 0

                return porcentaje
            else:
                return 0
        else:
            return 0

    def _get_days_discount(self):
        if self.partner_id.property_supplier_payment_term_id:
            plazos = self.partner_id.property_supplier_payment_term_id.line_ids
            fecha_factura = self.invoice_date
            if fecha_factura:
                fecha_actual = datetime.now().date()
                days = (fecha_actual - fecha_factura).days
                list_days = []
                for plazo in plazos:
                    if plazo.value == 'percent':
                        list_days.append(plazo.days)
                list_days.sort()
                dias = None
                for x in range(0, len(list_days)):
                    if x == 0:
                        if fecha_actual >= fecha_factura and fecha_actual <= fecha_factura +timedelta(days=list_days[x]):
                            dias = list_days[x]
                    else:
                        if fecha_actual > fecha_factura + timedelta(days=list_days[x-1]) and fecha_actual <= fecha_factura + timedelta(days=list_days[x]):
                            dias = list_days[x]
                return dias
            else:
                return 0
        else:
            return 0



    @api.depends('partner_id', 'invoice_date', 'amount_untaxed', 'payment_state', 'porc_financial_discount')
    def _compute_financial_discount(self):
        for move in self:
            if move.partner_id and move.payment_state != 'paid':
                if move.partner_id.property_supplier_payment_term_id:
                    fecha_actual = datetime.now().date()
                    fecha_factura = move.invoice_date
                    if fecha_factura:
                        days = (fecha_actual - fecha_factura).days
                        days_disc = move._get_days_discount()
                        if days_disc != None:
                            if days <= days_disc:
                                #move.financial_discount = move.amount_total - (move.amount_total * move._get_porcentaje_descuento() / 100)
                                move.financial_discount = move.amount_untaxed - (move.amount_untaxed * move._get_porcentaje_descuento() / 100)
                            else:
                                move.financial_discount = 0
                        else:
                            move.financial_discount = 0
                    else:
                        move.financial_discount=0
                else:
                    move.financial_discount = 0
            else:
                move.financial_discount = 0


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        if not res:
            res = {}
        if self.partner_id.property_supplier_payment_term_id:
            plazos = self.partner_id.property_supplier_payment_term_id.line_ids
            descuento = ''
            for plazo in plazos:
                if plazo.value == 'percent':
                    descuento += 'Descuento del '+ str(100 - plazo.value_amount) +'% si el pago se realiza antes de '+ str(plazo.days) +' dias \n'
            warning = {
                'title': 'Descuento financiero',
                'message': descuento,
                'type': 'notification',
            }
            res.update({
                'warning': warning
            })
        return res


    '''@api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        if not res:
            res = {}
        if self.type == 'in_invoice':
            if self.partner_id.financial_discount > 0:
                warning = {
                    'title': 'Descuento financiero',
                    'message': 'El proovedor posee un descuento financiero del  {}%'.format(
                        str(self.partner_id.financial_discount)),
                    'type': 'notification',
                }
                res.update({
                    'warning': warning
                })
        return res'''
