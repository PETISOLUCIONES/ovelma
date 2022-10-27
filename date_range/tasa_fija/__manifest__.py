# -*- coding: utf-8 -*-
{
    'name': 'Tasa fija',
    'author': 'PETI Soluciones Productivas',
    'category': 'Sale/subscription',
    'summary': 'Agregar una tasa fija para un cliente.',
    'description': """Agregar una tasa fija para un cliente.""",
    'depends': ['base', 'account', 'sale_subscription', 'sale_order_currency', 'sale_subscription_currency',
                'facturacion_electronica', 'account_invoice_change_currency'],
    'data': [
        'views/views.xml',
    ],
}
