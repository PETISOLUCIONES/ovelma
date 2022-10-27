# -*- coding: utf-8 -*-
{
    'name': "xdoo_sale_order_uniq_product",

    'summary': """
        Impide productos duplicados""",

    'description': """
        Impide productos duplicados
    """,

    'author': "FONSE SAS",
    'website': "http://www.experttys.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
 }