# -*- coding: utf-8 -*-
from odoo import http

# class MrpProductionReport(http.Controller):
#     @http.route('/mrp_production_report/mrp_production_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_production_report/mrp_production_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_production_report.listing', {
#             'root': '/mrp_production_report/mrp_production_report',
#             'objects': http.request.env['mrp_production_report.mrp_production_report'].search([]),
#         })

#     @http.route('/mrp_production_report/mrp_production_report/objects/<model("mrp_production_report.mrp_production_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_production_report.object', {
#             'object': obj
#         })