# -*- coding: utf-8 -*-
{
    'name': "descuentos_financieros",

    'summary': """
        Descuentos financieros""",

    'description': """
        Para los proveedores se agregan los campos de dias de descuento financiero y descuento financiero.
        Al registrar el pago se muestra el descuento financiero que tenga el proveedor si aplica
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
