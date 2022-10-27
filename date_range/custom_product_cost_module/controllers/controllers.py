# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request,Response
from odoo.tools import date_utils
import json
import logging

_logger = logging.getLogger(__name__)
class SyncWithDatabase(http.Controller):
    @http.route('/update/quants/', type='http', auth="none",methods=['POST','OPTIONS'],website=False, csrf=False,cors='*')
    def update_quants(self,**kwargs):

        
        records = request.env.cr.execute(f'''
                                    SELECT id
                                    FROM
                                    stock_quant 
                                ''')
        records = request.env.cr.dictfetchall()
        
        
        if records:
            for rec in records:
                request.env['product.locationwise.onhand'].sudo().create({"quant_reference_id":rec['id']})
                
        response = Response(
                        json.dumps(
                                    {
                                    'success':True
                                    },
                                    default=date_utils.json_default
                                    ),
                        content_type='application/json',
                        status=200
                                    
                    )
        response.status = '200'
        return response

    @http.route('/update/properties/', type='http', auth="none",methods=['POST','OPTIONS'],website=False, csrf=False,cors='*')
    def update_property(self,**kwargs):

        
        records = request.env.cr.execute(f'''
                                    select id,res_id from ir_property where name = 'standard_price' and res_id like 'product.product,%'
                                ''')
        records = request.env.cr.dictfetchall()
        
        
        if records:
            for rec in records:
                model_name,product_id = rec['res_id'].split(',')
                product = request.env['product.product'].sudo().search([('id','=',int(product_id))])
                if product:
                    request.env['product.cost.companywise'].sudo().create({"property_reference_id":rec['id']})
                
        response = Response(
                        json.dumps(
                                    {
                                    'success':True
                                    },
                                    default=date_utils.json_default
                                    ),
                        content_type='application/json',
                        status=200
                                    
                    )
        response.status = '200'
        return response


    @http.route('/create/dummy/quants/', type='http', auth="none",methods=['POST','OPTIONS'],website=False, csrf=False,cors='*')
    def create_stock_quants_for_dummy_location(self,**kwargs):

        
        records = request.env.cr.execute(f''' select distinct id as product_id from product_product ''')
        records = request.env.cr.dictfetchall()
        
        
        if records:
            for rec in records:
                properties = request.env.cr.execute(f'''
                                    select company_id from ir_property where name = 'standard_price' and res_id = 'product.product,{rec['product_id']}'
                                ''')
                properties = request.env.cr.dictfetchall()
                
                if properties:
                    for prop in properties:
                        quants = request.env['stock.quant'].sudo().search([('product_id','=', rec['product_id']),('company_id','=',prop['company_id'])])

                        if not quants:
                            loc = request.env['stock.location'].sudo().search([('name','=', f"techneith_cero_{prop['company_id']}")])
                            try:
                                q = request.env['stock.quant'].sudo().create({'location_id':loc.id,'product_id':rec['product_id'],'reserved_quantity':1,'is_dummy':True})
                            except Exception as e:
                                _logger.error(f"{rec['product_id']},{prop['company_id']},{str(e)}")
        response = Response(
                        json.dumps(
                                    {
                                    'success':True
                                    },
                                    default=date_utils.json_default
                                    ),
                        content_type='application/json',
                        status=200
                                    
                    )
        response.status = '200'
        return response

    
    @http.route('/create/dummy/locations', type='http', auth="none",methods=['POST','OPTIONS'],website=False, csrf=False,cors='*')
    def create_dummy_location(self,**kwargs):
        records = request.env.cr.execute(f''' select distinct id from res_company ''')
        records = request.env.cr.dictfetchall()

        for company in records:
            q = request.env['stock.location'].sudo().create({'name':f"techneith_cero_{company['id']}",'company_id':company['id']})
        response = Response(
                        json.dumps(
                                    {
                                    'success':True
                                    },
                                    default=date_utils.json_default
                                    ),
                        content_type='application/json',
                        status=200
                                    
                    )
        response.status = '200'
        return response