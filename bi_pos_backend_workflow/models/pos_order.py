from odoo import fields, models, api, _
from odoo.tools import float_is_zero


class PosOrder(models.Model):
	_inherit = "pos.order"

	def default_pricelist(self):
		return self.env['product.pricelist'].search([('company_id', 'in', (False, self.env.company.id)), ('currency_id', '=', self.env.company.currency_id.id)], limit=1)

	

	pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, 
		states={'draft': [('readonly', False)]}, readonly=True,default=default_pricelist)


	company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
	
	amount_return = fields.Float(string='Returned', digits=0, required=True, readonly=True,default=0)
	
	invoice_group = fields.Boolean(related="config_id.module_account", readonly=True)

	price_subtotal = fields.Float(string='Subtotal w/o Tax', digits=0)

	total_cost = fields.Float(string='Total cost', digits='Product Price', readonly=True)


	
	@api.onchange('payment_ids', 'lines')
	def _onchange_amount_all(self):
		for order in self:
			if order.pricelist_id:
				currency = order.pricelist_id.currency_id
			else:
				currency = self.env.user.currency_id
			order.amount_paid = sum(payment.amount for payment in order.payment_ids)
			order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.payment_ids)
			order.amount_tax = currency.round(sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
			amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
			order.amount_total = order.amount_tax + amount_untaxed


	@api.depends('price_subtotal' , 'total_cost')
	def _compute_margin(self):
		for line in self:
			line.margin = line.price_subtotal - line.total_cost
			line.margin_percent = not float_is_zero(line.price_subtotal, line.currency_id.rounding) and line.margin / line.price_subtotal or 0

	
		
	def print_receipt(self):
		return self.env.ref('bi_pos_backend_workflow.pos_receipt_backend_pos').report_action(self)



class PosOrderLine(models.Model):
	_inherit = "pos.order.line"


	tax_ids = fields.Many2many('account.tax', string='Taxes', readonly=False)

	currency_id = fields.Many2one('res.currency', related='order_id.currency_id')




	

