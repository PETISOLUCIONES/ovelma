# -*- coding: utf-8 -*-
# from odoo import http


# class AlquilerFacturacionElectronica(http.Controller):
#     @http.route('/alquiler_facturacion_electronica/alquiler_facturacion_electronica', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/alquiler_facturacion_electronica/alquiler_facturacion_electronica/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('alquiler_facturacion_electronica.listing', {
#             'root': '/alquiler_facturacion_electronica/alquiler_facturacion_electronica',
#             'objects': http.request.env['alquiler_facturacion_electronica.alquiler_facturacion_electronica'].search([]),
#         })

#     @http.route('/alquiler_facturacion_electronica/alquiler_facturacion_electronica/objects/<model("alquiler_facturacion_electronica.alquiler_facturacion_electronica"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('alquiler_facturacion_electronica.object', {
#             'object': obj
#         })
