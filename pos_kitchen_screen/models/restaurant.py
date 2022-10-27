# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import api, fields, models,_
import datetime
from functools import partial
import logging
_logger = logging.getLogger(__name__)


class PosKitchenOrder(models.Model):
	_name = 'pos.kitchen.order'
	_order = 'id desc'
	_rec_name = 'pos_reference'

	name = fields.Char(string="Name")
	is_changed = fields.Boolean(default=False,string="Es modificado")
	order_progress = fields.Selection([('cancel',"Cancelado"),('pending','Pendiente'),('done','Hecho'),('partially_done','Parcialmente Hecho'),('new','Nuevo')],string="Progreso Orden")
	config_id = fields.Many2one('pos.config',string="POS Config")
	session_id = fields.Many2one('pos.session',string="POS Sesion")
	is_state_updated = fields.Boolean(string="¿Está actualizado el estado?")
	kitchen_order_name = fields.Char(string="Token NO.")
	user_id = fields.Many2one('res.users',string="Usuarios")
	amount_total = fields.Float(string="Monto Total")
	out_of_stock_products = fields.One2many('product.product','related_kitchen_order',string="Productos agotados")
	cancellation_reason = fields.Char(string="Razon de cancelacion")
	pos_reference = fields.Char(string="Pos Referencia")
	partner_id = fields.Many2one('res.partner',string="Cliente")
	date_order = fields.Datetime(string="Fecha y hora")
	lines = fields.One2many('pos.kitchen.orderline','order_id',string="Líneas de pedido de cocina")
	order_type = fields.Selection([('pos','Punto de Venta'),('kitchen','Cocina')],string="Tipo de orden")
	is_kitchen_order = fields.Boolean(string="es orden de cocina")


class PosKitchenOrderLines(models.Model):
	_name = 'pos.kitchen.orderline'

	order_id = fields.Many2one('pos.kitchen.order',string="Orden POS relacionado")
	display_name = fields.Char(string="Nombre para mostrar")
	is_orderline_done = fields.Boolean(string="¿Está terminada la línea de pedido?",default=False)
	product_id = fields.Many2one('product.product',string="Producto")
	state = fields.Selection([('cancel',"Cancelado"),('in_process','En Proceso'),('done','Hecho'),('in_queue','En fila'),('new','Nuevo')],string="Estado",default="new")
	qty = fields.Integer(string="Cantidad")
	note = fields.Char(string="Nota")
	previous_quantity = fields.Integer(string="Cantidad anterior")
	previous_first_quantity = fields.Integer(string="Primera cantidad anterior")
	qty_added = fields.Integer(string="Cantidades añadidas")
	qty_removed = fields.Integer(string="Cantidades eliminadas")
	total_qtys = fields.Integer(string="Cantidades totales")
	price_unit = fields.Float(string="Precio")
	full_product_name = fields.Char(string="Nombre completo del producto")


class PosKitchenConfig(models.Model):
	_inherit = 'pos.kitchen.screen.config'

	is_changed = fields.Boolean(default=False,string="Es modificado")
