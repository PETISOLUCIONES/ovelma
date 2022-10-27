from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare
from datetime import datetime


class SaleInvoicePlan(models.Model):
    _name = "sale.invoice.plan"
    _description = "Invoice Planning Detail"
    _order = "installment"

    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sales Order",
        index=True,
        readonly=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        related="sale_id.partner_id",
        store=True,
        index=True,
    )
    state = fields.Selection(
        string="Status",
        related="sale_id.state",
        store=True,
        index=True,
    )
    installment = fields.Integer(string="Installment")
    plan_date = fields.Date(string="Plan Date", required=True)
    invoice_type = fields.Selection(
        [("advance", "Advance"), ("installment", "Installment")],
        string="Type",
        required=True,
        default="installment",
    )
    last = fields.Boolean(
        string="Last Installment",
        compute="_compute_last",
        help="Last installment will create invoice use remaining amount",
    )
    percent = fields.Monetary(
        string="Valor a pagar",
        digits="Product Unit of Measure",
        help="Valor que se pagará sin impuestos",
    )

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)

    invoice_move_ids = fields.Many2many(
        "account.move",
        relation="sale_invoice_plan_invoice_rel",
        column1="plan_id",
        column2="move_id",
        string="Invoices",
        readonly=True,
    )
    to_invoice = fields.Boolean(
        string="Next Invoice",
        compute="_compute_to_invoice",
        help="If this line is ready to create new invoice",
    )
    invoiced = fields.Boolean(
        string="Invoice Created",
        compute="_compute_invoiced",
        help="If this line already invoiced",
    )
    _sql_constraint = [
        (
            "unique_instalment",
            "UNIQUE (sale_id, installment)",
            "Installment must be unique on invoice plan",
        )
    ]

    def _compute_to_invoice(self):
        """If any invoice is in draft/open/paid do not allow to create inv.
        Only if previous to_invoice is False, it is eligible to_invoice.
        """
        for rec in self:
            rec.to_invoice = False
        for rec in self.sorted("installment"):
            if rec.state != "sale":  # Not confirmed, no to_invoice
                continue
            if not rec.invoiced:
                rec.to_invoice = True
                break

    def _compute_invoiced(self):
        for rec in self:
            invoiced = rec.invoice_move_ids.filtered(
                lambda l: l.state in ("draft", "posted")
            )
            rec.invoiced = invoiced and True or False
        for rec in self:
            if rec.plan_date < datetime.strptime('2022-08-01', '%Y-%m-%d').date()  or rec.invoiced:
                rec.invoiced = True

    def _compute_last(self):
        for rec in self:
            last = max(rec.sale_id.invoice_plan_ids.mapped("installment"))
            rec.last = rec.installment == last

    '''def _compute_new_invoice_quantity(self, invoice_move):
        self.ensure_one()
        if self.last:  # For last install, let the system do the calc.
            return
        percent = self.percent
        move = invoice_move.with_context({"check_move_validity": False})
        for line in move.invoice_line_ids:
            if not len(line.sale_line_ids) >= 0:
                raise UserError(_("No matched order line for invoice line"))
            order_line = fields.first(line.sale_line_ids)
            if order_line.is_downpayment:  # based on 1 unit
                line.write({"quantity": -percent / 100})
            else:
                plan_qty = order_line.product_uom_qty * (percent / 100)
                prec = order_line.product_uom.rounding
                if float_compare(plan_qty, line.quantity, prec) == 1:
                    raise ValidationError(
                        _(
                            "Plan quantity: %s, exceed invoiceable quantity: %s"
                            "\nProduct should be delivered before invoice"
                        )
                        % (plan_qty, line.quantity)
                    )
                line.write({"quantity": plan_qty})
        # Call this method to recompute dr/cr lines
        move._move_autocomplete_invoice_lines_values()'''




    def _compute_new_invoice_quantity(self, invoice_move):
        self.ensure_one()
        if self.last:  # For last install, let the system do the calc.
            #return
            self.sale_id.write({'invoice_status': 'invoiced'})
        percent = self.percent
        move = invoice_move.with_context({"check_move_validity": False})
        invoice_lines_group = {}
        invoice_ids = []
        for line in move.invoice_line_ids:
            if not len(line.sale_line_ids) >= 0:
                raise UserError(_("No matched order line for invoice line"))
            order_line = fields.first(line.sale_line_ids)
            invoice_ids += order_line.order_id.facturas_ids.ids
            order_line.order_id.write({'facturas_ids': [(4, move.id)]})
            future_flow = self.env["future.flow.line"].search(
                [('invoice_date', '=', self.plan_date), ('sale_rental_schedule_id', '=', order_line.id)])
            if order_line.is_downpayment:  # based on 1 unit
                line.write({"quantity": - sum(flow.percent_invoice for flow in future_flow)})
            elif order_line.is_rental:
                #plan_qty = order_line.product_uom_qty * (percent / 100)
                if order_line.product_uom_qty == order_line.qty_delivered > order_line.qty_returned:
                    plan_qty = sum(flow.percent_invoice for flow in future_flow)
                    if line.product_id.id in invoice_lines_group:
                        invoice_lines_group[line.product_id.id]['quantity'] += plan_qty
                        invoice_lines_group[line.product_id.id]['cantidad_real'] += 1
                    else:
                        invoice_lines_group[line.product_id.id] = {
                            'display_type': False if line.display_type else line.display_type,
                            'sequence': line.sequence,
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_uom_id.id,
                            'quantity': plan_qty,
                            'discount': line.discount,
                            'price_unit': line.price_unit,
                            'tax_ids': [(6, 0, line.tax_ids.ids)],
                            'analytic_account_id': line.analytic_account_id.id,
                            'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                            #'sale_line_ids': [(6, 0, [order_line.id])],
                            'move_id': line.move_id.id,
                            'cantidad_real': 1,
                            'rental': True,
                        }
                        if line.display_type:
                            invoice_lines_group[line.product_id.id]['account_id'] = False
                    #order_line.write({'qty_invoiced': order_line.qty_invoiced + plan_qty})
                    line.unlink()
                    '''plan_qty = sum(flow.percent_invoice for flow in future_flow)
                    prec = order_line.product_uom.rounding
                    if float_compare(plan_qty, line.quantity, prec) == 1:
                        raise ValidationError(
                            _(
                                "Plan quantity: %s, exceed invoiceable quantity: %s"
                                "\nProduct should be delivered before invoice"
                            )
                            % (plan_qty, line.quantity)
                        )
                    line.write({"quantity": plan_qty})'''
                else:
                    line.unlink()
        for line in invoice_lines_group:
            '''invoice_lines_group[line]['quantity'] = invoice_lines_group[line]['quantity']/invoice_lines_group[line]['cantidad_real']
            invoice_lines_group[line]['price_unit'] = invoice_lines_group[line]['price_unit']*invoice_lines_group[line]['cantidad_real']
            invoice_lines_group[line]['price_unit_real'] = invoice_lines_group[line]['price_unit']*invoice_lines_group[line]['quantity']/invoice_lines_group[line]['cantidad_real']'''
            invoice_lines_group[line]['price_unit'] = invoice_lines_group[line]['price_unit'] * invoice_lines_group[line]['quantity'] / invoice_lines_group[line]['cantidad_real']
            invoice_lines_group[line]['cantidad_alquiler'] = invoice_lines_group[line]['quantity']/invoice_lines_group[line]['cantidad_real']
            invoice_lines_group[line]['quantity'] = invoice_lines_group[line]['cantidad_real']
            move.write({'invoice_line_ids': [(0,0,invoice_lines_group[line])]})
                #line.write({"price_unit": future_flow.amount_payment})
        # Call this method to recompute dr/cr lines
        move._move_autocomplete_invoice_lines_values()
