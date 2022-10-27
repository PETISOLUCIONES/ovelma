# -*- coding: utf-8 -*-
{
    'name': "Importar Facturas Electronicas",

    'summary': """
            Importar facturas electronicas.""",

    'description': """
        Importar facturas electronicas a contabilidad/proveedores/facturas, a partir del xml..
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'account',
        'facturacion_electronica',
        'purchase',
    ],

    # always loaded
    'data': [
        #'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_import_xml.xml',

    ],
}
