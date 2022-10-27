# -*- coding: utf-8 -*-
# from odoo import http


# class PosInfoCustomerPeti(http.Controller):
#     @http.route('/pos_info_customer_peti/pos_info_customer_peti/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_info_customer_peti/pos_info_customer_peti/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_info_customer_peti.listing', {
#             'root': '/pos_info_customer_peti/pos_info_customer_peti',
#             'objects': http.request.env['pos_info_customer_peti.pos_info_customer_peti'].search([]),
#         })

#     @http.route('/pos_info_customer_peti/pos_info_customer_peti/objects/<model("pos_info_customer_peti.pos_info_customer_peti"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_info_customer_peti.object', {
#             'object': obj
#         })
