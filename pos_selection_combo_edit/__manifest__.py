# -*- coding: utf-8 -*-
{
    'name': 'POS Selection Combo Pack Edit',
    'summary': "Selection Combo pack is a combination of several products put together and allow to select from Products at a special price, also you can edit added items later",
    'description': """
POS Selection Combo Pack Edit.
===============================================
Selection Combo pack is a combination of several products put together and allow to select from Products at a special price.
combo pack is created to increase sales of the complementary products and to provide special offers to the customers.
With the help of POS Selection Combo Pack seller can sell products in packs as a combo product and allow facility to select products from it.
Once you Select items you can edit selected Items from combo pack.
    """,

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Point of Sale',
    'version': '13.0.0.1.0',
    'depends': ['pos_selection_combo'],

    'data': [
        'views/assets.xml',
        'views/pos_selection_combo_view.xml',
    ],

    'license': "OPL-1",
    'price': 40,
    'currency': "EUR",

    "installable": True,

    'images': ['static/description/main.png'],
    'live_test_url': 'https://youtu.be/DqTDsmzSLro',
}
