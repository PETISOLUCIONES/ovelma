# -*- coding: utf-8 -*-
# from odoo import http


# class ActualizarClientes(http.Controller):
#     @http.route('/actualizar_clientes/actualizar_clientes/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/actualizar_clientes/actualizar_clientes/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('actualizar_clientes.listing', {
#             'root': '/actualizar_clientes/actualizar_clientes',
#             'objects': http.request.env['actualizar_clientes.actualizar_clientes'].search([]),
#         })

#     @http.route('/actualizar_clientes/actualizar_clientes/objects/<model("actualizar_clientes.actualizar_clientes"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('actualizar_clientes.object', {
#             'object': obj
#         })
