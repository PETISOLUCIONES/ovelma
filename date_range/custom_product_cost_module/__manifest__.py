# -*- coding: utf-8 -*-
{
    'name': "Custom Product Module",

    'summary': """ this module is customization for stored computed fields and tables for tableau""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Techneith",
    'website': "https://www.techneith.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.4',

    # any module necessary for this one to work correctly
    'depends': ['base','account','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/cron.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
