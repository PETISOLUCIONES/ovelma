# -*- coding: utf-8 -*-
{
    'name': "pos_info_customer_peti",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'l10n_co_base_nit'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/assets.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'pos_info_customer_peti/static/src/xml/pos.xml',
        ],
        'point_of_sale.assets': [
            'pos_info_customer_peti/static/src/js/pos.js',
            'pos_info_customer_peti/static/src/js/ClientDetailsEdit.js',
            'pos_info_customer_peti/static/src/css/pos.css',
            ]
    },
}
