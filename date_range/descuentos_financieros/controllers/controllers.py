# -*- coding: utf-8 -*-
# from odoo import http


# class DescuentosFinancieros(http.Controller):
#     @http.route('/descuentos_financieros/descuentos_financieros/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/descuentos_financieros/descuentos_financieros/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('descuentos_financieros.listing', {
#             'root': '/descuentos_financieros/descuentos_financieros',
#             'objects': http.request.env['descuentos_financieros.descuentos_financieros'].search([]),
#         })

#     @http.route('/descuentos_financieros/descuentos_financieros/objects/<model("descuentos_financieros.descuentos_financieros"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('descuentos_financieros.object', {
#             'object': obj
#         })
