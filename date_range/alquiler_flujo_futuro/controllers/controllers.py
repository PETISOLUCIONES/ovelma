# -*- coding: utf-8 -*-
# from odoo import http


# class AlquilerFlujoFuturo(http.Controller):
#     @http.route('/alquiler_flujo_futuro/alquiler_flujo_futuro', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/alquiler_flujo_futuro/alquiler_flujo_futuro/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('alquiler_flujo_futuro.listing', {
#             'root': '/alquiler_flujo_futuro/alquiler_flujo_futuro',
#             'objects': http.request.env['alquiler_flujo_futuro.alquiler_flujo_futuro'].search([]),
#         })

#     @http.route('/alquiler_flujo_futuro/alquiler_flujo_futuro/objects/<model("alquiler_flujo_futuro.alquiler_flujo_futuro"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('alquiler_flujo_futuro.object', {
#             'object': obj
#         })
