{
    'name': 'Pagos Wompi',
    'author': 'PETI Soluciones Productivas',
    'category': 'Accounting/Payment',
    'summary': 'Metodos de pago: Wompi Colombia',
    'description': """Wompi Colombia""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_wompicol_templates.xml',
        'data/payment_acquirer_data.xml',
    ],

    'uninstall_hook': 'uninstall_hook',
}
