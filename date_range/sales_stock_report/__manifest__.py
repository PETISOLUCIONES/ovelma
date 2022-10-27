# -*- coding: utf-8 -*-
{
    'name' : 'Sale Stock Report',
    'version' : '13.1',
    'summary': 'Custom Stock report',
    'sequence': 1,
    'author': 'Paras sutariya / paras.sutariya125@gmail.com',
    'description': """Sale Stock Report for current on hand Qty and Current Month's delivered Qty""",
    'category': 'Reporting',
    'website': '',
    'depends' : [
        'base_setup',
        'product',
        'account',
        'stock',
        'sale_stock',
        'sale_management'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/report_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
