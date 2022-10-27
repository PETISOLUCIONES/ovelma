# -*- coding: utf-8 -*-
{
    'name': "mrp_production_report",

    'summary': """
        Lista todas las materias primas necesarias para una produccion""",

    'description': """
        Lista todas las materias primas necesarias para una produccio
    """,

    'author': "Carlos Fonseca",
    'website': "http://www.xdoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'mrp',
    ],

    'images': [
            'static/description/icon.png',
    ],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        #'views/templates.xml',
        'report/mrp_production_report_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}