# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError, Warning,UserError
from odoo.http import request
import datetime
import json
import logging
_logger = logging.getLogger(__name__)


class PosScreenConfig(models.Model):
	_name = 'pos.kitchen.screen.config'
	_description = 'Configuracion cocina'

	name = fields.Char(string="Nombre")
	url = fields.Char(string="Url de visualización de cocina",compute="compute_url")
	config_related_id = fields.Many2one('pos.config',string="Pos Config")
	pos_config_ids = fields.Many2many('pos.config',string="POS permitido")
	pos_category_ids = fields.Many2many('pos.category',string="Categorias POS permitidas")
	ip_address = fields.Char(string="Direccion IP")
	orders_on_grid = fields.Selection([('2',2),('3',3),('4',4),('6',6)],string="Órdenes en la cuadrícula de la pantalla",default="3")
	queue_order = fields.Selection([('new2old',"Más nueva a más vieja"),('old2new',"Más vieja a más nueva")],default="new2old")

	@api.depends('pos_config_ids')
	def compute_url(self):
		for self_obj in self:
			data = None
			url = ''
			if(self_obj.ip_address):
				data = self_obj.ip_address
				url = 'http://{}/pos/kitchen/{}/screen'.format(data,self_obj.id)
			else:
				data = request.httprequest.host_url
				url = '{}pos/kitchen/{}/screen'.format(data,self_obj.id)
			self_obj.url = url



	def redirect_customer_screen(self):
		if self.url:
			url = self.url
		else:
			base_url = request.httprequest.host_url
			url = '{}pos/kitchen/{}/screen'.format(base_url,self.id)
		return {
				"type": "ir.actions.act_url",
				"url": url,
				"target": "new",
				}


class PosConfig(models.Model):
	_inherit = 'pos.config'

	pos_kitchen_screen = fields.Many2many('pos.kitchen.screen.config', string="Pos pantalla cocina")
	auto_accept = fields.Boolean('Aceptar orden de cocina automáticamente',default=False)


	def open_screen_configuration(self):
		view_id_tree = self.env.ref('pos_kitchen_screen.pos_screen_conf_form').id
		pos_screen_data = self.env['pos.kitchen.screen.config'].search([("pos_config_ids",'=ilike',self.id)])
		if pos_screen_data and pos_screen_data.id:
			return {
				'type': 'ir.actions.act_window',
				'res_model': 'pos.kitchen.screen.config',
				'view_mode': 'form',
				'res_id':pos_screen_data.id,
				'view_id':view_id_tree,
				'target': 'current'
			}
		else:
			raise Warning("No Kitchen Screen Settings available for this POS.")

class ProductProduct(models.Model):
	_inherit = "product.product"

	related_order = fields.Many2one('pos.order',string="Orden relacionada")
	related_kitchen_order = fields.Many2one('pos.kitchen.order',string="Orden de cocina relacionado")


class PosOrderLine(models.Model):
	_inherit = 'pos.order.line'

	is_orderline_done = fields.Boolean(string="¿Está terminada la línea de pedido?",default=False)
	state = fields.Selection([('cancel',"Cancelado"),('in_process','En Proceso'),('done','Hecho'),('in_queue','En fila'),('new','Nueva')],string="State",default="new")


class PosOrder(models.Model):
	_inherit = 'pos.order'

	order_progress = fields.Selection([('cancel',"Cancelado"),('pending','Pendiente'),('done','Hecho'),('partially_done','Parcialmente hecho'),('new','Nuevo')],string="Order Progress")
	screen_progress = fields.Text(string="Progreso de la pantalla")
	kitchen_order_name = fields.Char(string="Orden de cocina")
	cancellation_reason = fields.Char(string="Razon de cancelacion")
	is_state_updated = fields.Boolean(string="¿Está actualizado el estado?")
	out_of_stock_products = fields.One2many('product.product','related_order',string="Producto agotado")

	@api.model
	def get_token_number(self):
		token = ''
		sequence_date_wise = self.env['token.perday'].search([],limit=1)
		if len(sequence_date_wise) == 0:
			self.env['token.perday'].search([]).unlink()
			sequence_date_wise = self.env['token.perday'].create({
				'name':"token"+datetime.date.today().strftime("%Y-%m-%d")
			})
		token = sequence_date_wise.sequence_id._next()
		return token



	# @api.model
	# def _order_fields(self,ui_order):
	# 	fields_return = super(PosOrder,self)._order_fields(ui_order)
	# 	config_id = self.env['pos.session'].browse(ui_order['pos_session_id']).config_id
	# 	if ui_order.get('is_kitchen_order') and not config_id.module_pos_restaurant:
	# 		sequence_date_wise = self.env['token.perday'].search([('date_token','>=',fields.Date.to_string((datetime.date.today())))])
	# 		if sequence_date_wise:
	# 			fields_return.update({'kitchen_order_name':sequence_date_wise.sequence_id._next(),
	# 				'order_progress':'pending'
	# 			})
	# 		else:
	# 			self.env['token.perday'].search([]).unlink()
	# 			sequence_date_wise = self.env['token.perday'].create({
	# 				'name':"token"+datetime.date.today().strftime("%Y-%m-%d")
	# 			})
	# 			fields_return.update({'kitchen_order_name':sequence_date_wise.sequence_id._next(),
	# 				'order_progress':'pending'
	# 			})
	# 	return fields_return


	@api.model
	def _order_fields(self,ui_order):
		fields_return = super(PosOrder,self)._order_fields(ui_order)
		#_logger.info("kithen-order---%r",ui_order)
		session = self.env['pos.session'].sudo().browse(ui_order.get('pos_session_id'))
		#_logger.info('-------------------77777--%r',(hasattr(session.config_id,'order_acti,on')),session.config_id.order_action!='order_button',not hasattr(session.config_id,'order_action'))
		if(hasattr(session.config_id,'order_action') and session.config_id.order_action!='order_button') or not hasattr(session.config_id,'order_action'):
			fields_return.update({
				#'is_kitchen_order':ui_order.get('is_kitchen_order'),
				'kitchen_order_name':ui_order.get('token_no'),
				'order_progress':'pending' if session.config_id.auto_accept else 'new'
			})
			if(hasattr(session.config_id,'order_action')):
				fields_return.update({
					'is_kitchen_order':ui_order.get('is_kitchen_order')})
		return fields_return


	@api.model
	def fetch_updated_orders(self,config,order_ref):
		config_id = self.env['pos.config'].browse(config)
		order = False
		result = {
			'orders':{},
			'ref_wise_token':{},
			'ref_wise_progress':{},
			'time':False,
			'updated_state':False
		}
		orders = []
		if config_id:
			# if config_id.module_pos_restaurant:
			if hasattr(config_id,'order_action') and config_id.order_action == 'order_button':
				orders = self.env['pos.kitchen.order'].search([('date_order', '>=', datetime.date.today()),('config_id','=',config_id.id),('is_state_updated','=',True)])
				order = self.env['pos.kitchen.order'].search([('pos_reference', 'in', order_ref)])
			else:
				orders = self.env['pos.order'].search([('date_order', '>=', datetime.date.today()),('config_id','=',config_id.id),('is_state_updated','=',True)])
				order = self.env['pos.order'].search([('pos_reference','in',order_ref)])
		if orders:
			time_obj = datetime.datetime.now()
			current_time = time_obj.strftime("%H:%M:%S")
			result['time'] = current_time
			for order in orders:
				result['orders'][order.kitchen_order_name] = [order.order_progress,order.name]
				order.is_state_updated = False
		if order:
			for obj in order:
				result['ref_wise_progress'][obj.pos_reference] = [obj.order_progress,obj.kitchen_order_name]


		return result






	@api.model
	def create_from_ui(self, orders, draft=False):
		order_ids = super(PosOrder, self).create_from_ui(orders,draft)
		#_logger.info('--order_ids---%r',order_ids)
		for order_id in order_ids:
			order_list = []
			order_line_list = []
			payment_list = []
			has_category_product = []
			if(order_id.get('id')):
				order = self.browse([order_id.get('id')])
				config_id = order.config_id
				temp_screen_progress = {}
				# if not config_id.module_pos_restaurant:
				if not (hasattr(config_id,'order_action') and config_id.order_action == 'order_button'):
					if config_id.auto_accept:
						order.lines.write({'state':'in_process'})
				if not (hasattr(config_id,'order_action') and config_id.order_action == 'validation') or not config_id.module_pos_restaurant:
					pos_screen_data = self.env['pos.kitchen.screen.config'].search([("pos_config_ids",'=ilike',config_id.id)])
					is_allowed_order = True
					pos_categ_ids = self.env['pos.category']
					for data in pos_screen_data:
						pos_categ_ids += data.pos_category_ids
					if len(pos_screen_data):
						for data in pos_screen_data:
							for line in order.lines:
								for cat in line.product_id.pos_categ_id:
									if cat.id in data.pos_category_ids.ids:
										has_category_product.append(line.product_id)
										if data.id not in temp_screen_progress:
											temp_screen_progress[data.id] = 'new'
						if len(has_category_product) == 0:
							is_allowed_order = False
					screen_progress = json.dumps(temp_screen_progress)
					if is_allowed_order:
						order.screen_progress = screen_progress
						vals = {}
						vals['lines'] = []
						vals['name'] = order.name
						vals['screen_progress'] = screen_progress
						vals['amount_total'] = order.amount_total
						vals['pos_reference'] = order.pos_reference
						vals['order_progress'] = order.order_progress
						if has_category_product:
							vals['total_items'] = len(has_category_product)
						else:
							vals['total_items'] = sum([l.qty for l in order.lines])
						vals['date_order'] = order.date_order
						vals['kitchen_order_name'] = order.kitchen_order_name
						if order.partner_id:
							vals['partner_id'] = [order.partner_id.id, order.partner_id.name]
						else:
							vals['partner_id'] = False
						vals['id'] = order.id
						for line in order.lines:
							if line.product_id.pos_categ_id in pos_categ_ids:
								vals['lines'].append(line.id)
								line_vals = {}
								line_vals['display_name'] = line.display_name
								line_vals['id'] = line.id
								line_vals['order_id'] = [line.order_id.id, line.order_id.name]
								line_vals['price'] = line.price_subtotal_incl
								line_vals['product_id'] = [line.product_id.id, line.product_id.name]
								line_vals['qty'] = line.qty
								order_line_list.append(line_vals)
						order_list.append(vals)
			order_id['orders'] = order_list
			order_id['orderlines'] = order_line_list

		return order_ids



	@api.model
	def update_order_progress(self,data):
		order_progresses = []
		if len(data):
			int_list = [int(i) for i in data]
			orders = self.browse(int_list)
			order_progresses = orders.read(['order_progress'])
		return order_progresses




class TokenPerDay(models.Model):
	_name = "token.perday"

	name = fields.Char(string="nombre")
	sequence_id = fields.Many2one('ir.sequence', string='Kitchen Order IDs Sequence', readonly=True,
		help="Esta secuencia es creada automáticamente por Odoo pero puedes cambiarla"
			"para personalizar los números de referencia de sus pedidos de cocina.", copy=False, ondelete='restrict')

	date_token = fields.Date(string="Fecha para la secuencia de tokens",default=datetime.date.today())

	@api.model
	def create(self, values):
		IrSequence = self.env['ir.sequence'].sudo()
		val = {
			'name': _('POS Kitchen Order %s') % values.get('name'),
			'padding': 4,
			'prefix':"#",
			'code': "pos.kitchen.screen.config",
		}
		sequence = IrSequence.create(val)
		values['sequence_id'] = sequence.id
		res = super(TokenPerDay, self).create(values)
		return res
