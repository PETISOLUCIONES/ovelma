# -*- coding: utf-8 -*-
# Copyright 2019 NMKSoftware
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Localizacion Base - Colombia',
    'summary': 'Localizacion Base - Colombia',
    'author': 'NMKSoftware',
    'maintainer': 'NMKSoftware',
    'website': '',
    'version': '14.0.1.0.0',
    'category': 'Localization',
    'depends': [
        'base',
        'account',
        'account_tax_python',
        'l10n_co',
        'base_address_city',
    ],
    'data': [
        'data/res.city.csv',
        'data/res.bank.csv',
        'data/res.ciiu.csv',
        'data/account_tax_group.xml',
        'data/res_country_state.xml',
        'security/ir.model.access.csv',
        'views/res_ciiu_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/res_country_view.xml',
        'views/res_country_state.xml',
        'views/account_tax_view.xml',
        'views/account_journal_view.xml',
        'views/account_invoice_view.xml',
        'views/product_category_view.xml',
        'views/report_invoice_document.xml',
        'views/res_bank.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}
