# -*- coding: utf-8 -*-
{
    'name': "Descuento Plantilla",

    'summary': """
        Agregar los campos descuento y precio unitario en la plantilla de presupuesto""",

    'description': """
        Agregar los campos descuento y precio unitario en la plantilla de presupuesto
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale_management'],

    # always loaded
    'data': [
        'views/sale_order_template.xml',
    ],


}
