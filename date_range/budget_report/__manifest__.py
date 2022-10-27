{
    'name': "Budget Report",

    'summary': """
        A custom report for setting up budgets.
    """,

    'description': """
        A custom report for setting up budgets.
    """,

    'author': "Techneith ",
    'website': "http://www.techneith.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'contacts', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],

    'web.assets_frontend': [
        '/budget_report/static/scss/main.scss',
        '/budget_report/static/js/main.js',
    ],

    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
