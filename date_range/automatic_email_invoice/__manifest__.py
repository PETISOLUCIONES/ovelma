# -*- coding: utf-8 -*-
{
    'name': "Importar Facturas Electronicas de un servidor de correos",

    'summary': """
            Importar facturas electronicas desde un servidor de correos.""",

    'description': """
        Importar facturas electronicas a contabilidad/proveedores/facturas, a partir un servidor de correo
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'facturacion_electronica',
        'import_fac_electronica',
        'acuse',
    ],

    # always loaded
    'data': [
        #'security/security.xml',
        'data/mail_template.xml',
        'views/views.xml',
        'views/res_config_settings_view.xml',
    ],
}
