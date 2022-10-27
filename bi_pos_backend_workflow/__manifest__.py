# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Backend Workflow',
    'version': '15.0.0.0',
    'category': 'Point of Sale',
    'summary': 'Point of Sale backend flow POS backend workflow pos backend flow point of sales backend workflow point of sale backend workflow on pos sale backend workflow on point of sales pos invoice workflow pos invoice backend workflow process on pos order backend',
    'description' :"""
         This odoo app helps user to manage point of sale order also from backend instead of point of sale screen (front-end). User can select session, customer and create point of sale order with selected product, create payment for pos order, view created picking order, create and validate invoice, return order and print pos order receipt from backend. 
    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.in',
    "price": 49,
    "currency": 'EUR',
    'depends': ['point_of_sale'],
    'data': [
        'report/report.xml',
        'report/pos_receipt_view.xml',
        'views/models_view.xml',
    ],
    "license": "OPL-1",
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/JQGnilrnkpE',
    "images":['static/description/Banner.png'],
}
