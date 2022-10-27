# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round

dict_meses = {'enero': '01',
              'febrero': '02',
              'marzo': '03',
              'abril': '04',
              'mayo': '05',
              'junio': '06',
              'julio': '07',
              'agosto': '08',
              'septiembre': '09',
              'octubre': '10',
              'noviembre': '11',
              'diciembre': '12',
              'January': '01',
              'February': '02',
              'March': '03',
              'April': '04',
              'May': '05',
              'June': '06',
              'July': '07',
              'August': '08',
              'September': '09',
              'October': '10',
              'November': '11',
              'December': '12'
              }

dict_meses_ab = {'ene.': '01',
                 'feb.': '02',
                 'mar.': '03',
                 'abr.': '04',
                 'may.': '05',
                 'jun.': '06',
                 'jul.': '07',
                 'ago.': '08',
                 'sep.': '09',
                 'oct.': '10',
                 'nov.': '11',
                 'dic.': '12', }


class RentalProcessingLine(models.TransientModel):
    _inherit = 'rental.order.wizard.line'

    def _apply(self):
        res = super(RentalProcessingLine, self)._apply()
        for wizard_line in self:
            order_line = wizard_line.order_line_id
            if wizard_line.status == 'pickup' and wizard_line.qty_delivered > 0:
                order_line.order_id.use_invoice_plan = True
                order_line.order_id.create_invoice_plan()
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_plan_ids = fields.One2many(
        comodel_name="sale.invoice.plan",
        inverse_name="sale_id",
        string="Inovice Plan",
        copy=False,
    )
    use_invoice_plan = fields.Boolean(
        string="Use Invoice Plan",
        default=False,
        copy=False,
    )
    ip_invoice_plan = fields.Boolean(
        string="Invoice Plan In Process",
        compute="_compute_ip_invoice_plan",
        help="At least one invoice plan line pending to create invoice",
    )

    facturas_ids = fields.Many2many("account.move", string='Invoices', copy=False)

    def _get_invoiced(self):
        res = super()._get_invoiced()
        for order in self:
            invoices = order.facturas_ids.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            for invoice in invoices:
                if invoice not in order.invoice_ids:
                    order.invoice_ids += invoice
                    order.invoice_count += len(invoice)

    def create_invoice_auto(self, fecha=None):
        date_now = fields.Date.today() if not fecha else datetime.strptime(fecha, '%Y-%m-%d').date()
        invoice_plan = self.env['sale.invoice.plan'].search([('sale_id.is_rental_order', '=', True),
                                                             ('sale_id.state', 'in', ['sale']),
                                                             ('plan_date', '=', date_now),
                                                             ('invoiced', '=', False),
                                                             ('to_invoice', '=', True),
                                                             ('sale_id.rental_status', 'in', ['return'])])
        order_ids = []
        for plan in invoice_plan:
            order_ids.append(plan.sale_id.id)

        orders = self.env['sale.order'].search([('id', 'in', order_ids)])
        for order in orders:
            order.create_invoices_by_plan()

    def create_invoices_by_plan(self):
        sale = self.env["sale.order"].browse(self.id)
        sale.ensure_one()
        MakeInvoice = self.env["sale.advance.payment.inv"]
        invoice_plans = (
                self._context.get("all_remain_invoices")
                and sale.invoice_plan_ids.filtered(lambda l: not l.invoiced)
                or sale.invoice_plan_ids.filtered("to_invoice")
        )
        for plan in invoice_plans.sorted("installment"):
            makeinv_wizard = {"advance_payment_method": "delivered"}
            if plan.invoice_type == "advance":
                makeinv_wizard["advance_payment_method"] = "percentage"
                makeinv_wizard["amount"] = plan.percent
            makeinvoice = MakeInvoice.create(makeinv_wizard)
            makeinvoice.with_context(invoice_plan_id=plan.id, active_ids=[self.id]).create_invoices()
        return {"type": "ir.actions.act_window_close"}

    def _compute_ip_invoice_plan(self):
        for rec in self:
            has_invoice_plan = rec.use_invoice_plan and rec.invoice_plan_ids
            to_invoice = rec.invoice_plan_ids.filtered(lambda l: not l.invoiced)
            if rec.state == "sale" and has_invoice_plan and to_invoice:
                if rec.invoice_status == "to invoice" or (
                        rec.invoice_status == "no"
                        and "advance" in to_invoice.mapped("invoice_type")
                ):
                    rec.ip_invoice_plan = True
                    continue
            rec.ip_invoice_plan = False

    @api.constrains("state")
    def _check_invoice_plan(self):
        for rec in self:
            if rec.state != "draft":
                if rec.invoice_plan_ids.filtered(lambda l: not l.percent):
                    raise ValidationError(
                        _("Please fill percentage for all invoice plan lines")
                    )

    def action_confirm(self):
        if self.filtered(lambda r: r.use_invoice_plan and not r.invoice_plan_ids):
            raise UserError(_("Use Invoice Plan selected, but no plan created"))
        self.use_invoice_plan = True
        self.create_invoice_plan()
        res = super().action_confirm()
        return res

    def create_invoice_plan(self):
        self.ensure_one()
        invoice_plan_not_invoided = self.env['sale.invoice.plan'].search(
            [('invoice_move_ids', '=', False), ('id', 'in', self.invoice_plan_ids.ids)])
        this_installment = len(self.env['sale.invoice.plan'].search(
            [('invoice_move_ids', '!=', False), ('id', 'in', self.invoice_plan_ids.ids)]))
        invoice_plan_not_invoided.unlink()
        # self.invoice_plan_ids.unlink()
        flow_line_ids = []
        invoice_plans = []
        '''flow_lines_ini = self.env['future.flow.line'].search([('sale_rental_schedule_id', 'in', self.order_line.ids)],
                                                         order='invoice_date asc', limit=1)
        flow_lines_fin = self.env['future.flow.line'].search([('sale_rental_schedule_id', 'in', self.order_line.ids)],
                                                             order='invoice_date desc', limit=1)'''

        if self.invoice_pickup:
            group = 'invoice_date:day'
            format_date = '%d %m %Y'
        else:
            group = 'invoice_date'
            format_date = '%d %m %Y'

        flow_lines = self.env['future.flow.line'].read_group([('sale_rental_schedule_id', 'in', self.order_line.ids)],
                                                             fields=['invoice_date'],
                                                             groupby=[group])

        # installment_date = flow_lines_ini.invoice_date

        total_no_rental = sum(line.price_unit if not line.is_rental else 0 for line in self.order_line)
        day = self.recurrent_date_invoice.day
        for line in flow_lines:
            if not self.invoice_pickup:
                list_date = line['invoice_date'].split(' ')
                str_month = dict_meses[list_date[0]]
                str_year = list_date[1]
                invoice_date = datetime.strptime(str(day) + " " + str_month + " " + str_year, format_date)
            else:
                list_date = line['invoice_date:day'].split(' ')
                str_day = list_date[0]
                str_month = dict_meses_ab[list_date[1]]
                str_year = list_date[2]
                invoice_date = datetime.strptime(str_day + " " + str_month + " " + str_year, format_date)
            count_plan = self.env['sale.invoice.plan'].search_count(
                [('plan_date', '=', invoice_date), ('id', 'in', self.invoice_plan_ids.ids)])
            if count_plan == 0:
                this_installment += 1
                flow_lines_fin = self.env['future.flow.line'].search(
                    [('sale_rental_schedule_id', 'in', self.order_line.ids), ('invoice_date', '=', invoice_date)])

                value_to_pay = sum(
                    flow.amount_payment for flow in flow_lines_fin) + total_no_rental if this_installment == 1 else sum(
                    flow.amount_payment for flow in flow_lines_fin)
                # percent = sum(flow.sale_rental_schedule_id.price_subtotal * flow.percent_invoice for flow in flow_lines_fin)
                vals = {
                    "installment": this_installment,
                    "plan_date": invoice_date,
                    "invoice_type": "installment",
                    "percent": value_to_pay,
                }
                invoice_plans.append((0, 0, vals))
        self.write({"invoice_plan_ids": invoice_plans})
        return True

    def remove_invoice_plan(self):
        self.ensure_one()
        self.invoice_plan_ids.unlink()
        return True

    @api.model
    def _next_date(self, installment_date, interval, interval_type):
        installment_date = fields.Date.from_string(installment_date)
        if interval_type == "month":
            next_date = installment_date + relativedelta(months=+interval)
        elif interval_type == "year":
            next_date = installment_date + relativedelta(years=+interval)
        else:
            next_date = installment_date + relativedelta(days=+interval)
        next_date = fields.Date.to_string(next_date)
        return next_date

    def _create_invoices(self, grouped=False, final=False):
        moves = super()._create_invoices(grouped=grouped, final=final)
        invoice_plan_id = self._context.get("invoice_plan_id")
        if invoice_plan_id:
            plan = self.env["sale.invoice.plan"].browse(invoice_plan_id)
            moves.ensure_one()  # Expect 1 invoice for 1 invoice plan
            plan._compute_new_invoice_quantity(moves[0])
            moves.invoice_date = plan.plan_date
            plan.invoice_move_ids += moves
            moves.invoice_period = str(plan.installment)
            if moves.partner_id.facturacion_automatica:
                moves.action_post()
                if moves.state == 'posted':
                    moves.write({'invoice_batch': True})
        return moves


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cantidad_facturada = fields.Float(string='Invoiced Quantity',
                                      digits='Product Unit of Measure')

    def _get_invoice_lines(self):
        self.ensure_one()
        if self.order_id.is_rental_order:
            if self._context.get('accrual_entry_date'):
                return self.order_id.facturas_ids.invoice_line_ids.filtered(
                    lambda l: l.move_id.invoice_date and l.move_id.invoice_date <= self._context['accrual_entry_date']
                )
            else:
                return self.order_id.facturas_ids.invoice_line_ids
        else:
            return super()._get_invoice_lines()

    @api.depends('order_id.facturas_ids.invoice_line_ids.move_id.state',
                 'order_id.facturas_ids.invoice_line_ids.quantity',
                 'untaxed_amount_to_invoice',
                 'order_id.facturas_ids.invoice_line_ids.cantidad_alquiler', )
    def _compute_qty_invoiced(self):
        res = super()._compute_qty_invoiced()
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line._get_invoice_lines():
                if invoice_line.product_id == line.product_id:
                    if invoice_line.move_id.state != 'cancel':
                        if invoice_line.move_id.move_type == 'out_invoice':
                            if invoice_line.rental:
                                qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                                    invoice_line.cantidad_alquiler,
                                    line.product_uom)
                            else:
                                qty_invoiced += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity,
                                                                                              line.product_uom)
                        elif invoice_line.move_id.move_type == 'out_refund':
                            qty_invoiced -= invoice_line.product_uom_id._compute_quantity(invoice_line.quantity,
                                                                                          line.product_uom)
            line.qty_invoiced = qty_invoiced
