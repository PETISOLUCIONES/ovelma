# -*- coding: utf-8 -*-
{
    'name': "Crear Order de Compra Alquiler",

    'summary': """
        Crea ordenes de compra de manera automatica si no se cuenta con unidades disponibles para alquilar""",

    'description': """
        Crea ordenes de compra de manera automatica si no se cuenta con unidades disponibles para alquilar
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale_renting', 'purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/supplierinfo_data.xml',
    ],
}
