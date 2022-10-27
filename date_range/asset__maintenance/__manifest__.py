# -*- coding: utf-8 -*-
{
    'name': "Asset_Maintenance",

    'summary': """
        Mantenimiento de activos """,

    'description': """
        Modulo que agrega los campos de información del mantenimiento de activos, a la opción contabilidad->activos.
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account_asset', 'product_brand'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_asset_views.xml',
        'views/templates.xml',
    ],
}
