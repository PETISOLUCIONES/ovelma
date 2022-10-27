# -*- coding: utf-8 -*-
from odoo import http

# class XdooSaleOrderUniqProduct(http.Controller):
#     @http.route('/xdoo_sale_order_uniq_product/xdoo_sale_order_uniq_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/xdoo_sale_order_uniq_product/xdoo_sale_order_uniq_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('xdoo_sale_order_uniq_product.listing', {
#             'root': '/xdoo_sale_order_uniq_product/xdoo_sale_order_uniq_product',
#             'objects': http.request.env['xdoo_sale_order_uniq_product.xdoo_sale_order_uniq_product'].search([]),
#         })

#     @http.route('/xdoo_sale_order_uniq_product/xdoo_sale_order_uniq_product/objects/<model("xdoo_sale_order_uniq_product.xdoo_sale_order_uniq_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('xdoo_sale_order_uniq_product.object', {
#             'object': obj
#         })