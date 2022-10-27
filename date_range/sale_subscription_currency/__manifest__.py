

{
    'name': 'Cotizaciones de Venta en Otra Moneda',
    'version': '1.0',
    'category': 'Sale',
    'license': 'AGPL-3',
    'summary': 'Suscripciones en Otra Moneda',
    'author': 'PETI Soluciones productivas',
    'website': 'http://peti.com.co',
    'depends': ['base', 'sale_subscription', 'account', 'sale_order_currency'],
    'data': [
        'views/sale_subscription_views.xml',
        'views/partner_view.xml',
    ],
    'installable': True,
}
