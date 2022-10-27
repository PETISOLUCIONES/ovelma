# -*- coding: utf-8 -*-
{
    'name': "Conexon Beertuoso SMARTRENT",

    'summary': """
        Conexion webservice beertusos""",

    'description': """
        Conexion webservice beertusos
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale_renting',
                'l10n_co_location',
                'alquiler_flujo_futuro',
                'l10n_co_base_nit',
                'product_brand',
                'account_payment_partner'
                ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/rental_order_form.xml',
    ],
    # only loaded in demonstration mode

}
