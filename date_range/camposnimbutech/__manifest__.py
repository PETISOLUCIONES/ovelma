# -*- coding: utf-8 -*-
{
    'name': "Campos de Nimbutech",

    'summary': """
        Agregar campos al módelo res.partner""",

    'description': """
        Agregar campos al módelo res.partner
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'contacts'],

    # always loaded
    'data': [
        'views/res_partner_view.xml'
    ],

}
