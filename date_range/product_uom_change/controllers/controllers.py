# -*- coding: utf-8 -*-
# from odoo import http


# class ProductUomChange(http.Controller):
#     @http.route('/product_uom_change/product_uom_change', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_uom_change/product_uom_change/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_uom_change.listing', {
#             'root': '/product_uom_change/product_uom_change',
#             'objects': http.request.env['product_uom_change.product_uom_change'].search([]),
#         })

#     @http.route('/product_uom_change/product_uom_change/objects/<model("product_uom_change.product_uom_change"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_uom_change.object', {
#             'object': obj
#         })
