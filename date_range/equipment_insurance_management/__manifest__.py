# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.

{
    'name':'Equipments Insurance Management',
    'version':'2.2.7',
    'price': 99.0,
    'category': 'Human Resources',
    'currency': 'EUR',
    'license': 'Other proprietary',
    'summary': 'This app allow you to create Insurance of your Equipments and renewals.',
    'description': """
Maintenance
Insurance
health Insurance
Insurance odoo
erp Insurance
Insurance Management Systems
Insurance Management System
Property Insurance
risk management
Liability Insurance
risk Insurance
Insurance providers
Insurance provider
Equipments
Equipment
odoo Equipments
Equipments insurance
Equipment Checklist
Equipments
Insurance
asset Insurance
Equipment Maintenance Software
Equipment management
Insurance asset
product Insurance
item Insurance
Insurance Property
Purchase
Purchase/Configuration
Purchase/Configuration/Settings
Print Insurance Report
            """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'http://www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/12.png'],
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/equipment_insurance_management/828',#'https://youtu.be/AqDWuNYH-dc',
    'depends': [
        'account_accountant',
        'portal',
        'purchase',
        'account_asset',
        'l10n_co_location',
        'l10n_co_base_nit',
        'base',
        'asset__maintenance',
    ],
    'data':[
        'security/insurance_security.xml',
        'security/ir.model.access.csv',
        'data/insurance_policy_expire.xml',
        'data/insurance_policy_reminder.xml',
        'wizard/policy_renew.xml',
        'wizard/report_wizard.xml',
        'views/maintenance_equipment_view.xml',
        'views/equipment_insurance.xml',
        'views/insurance_property.xml',
        'views/policy_res_configuration.xml',
        'views/res_partner.xml',
        'report/insurance.xml',
        'report/report_reclamacion.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
