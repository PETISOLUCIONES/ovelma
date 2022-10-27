# -*- coding: utf-8 -*-
{
    'name': "Flujo futuro",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale_renting', 'sale_stock_renting'],
    'external_dependencies': {
        'python': ['pandas', 'openpyxl'],
    },
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/rental_order_form.xml',
        'views/res_partner.xml',
        'views/account_move.xml',
        'report/rental_report.xml',
        #'views/alquiler_template.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
'assets': {
        'web.assets_backend': [
            'alquiler_flujo_futuro/static/src/**/*',
        ],
    },

}
