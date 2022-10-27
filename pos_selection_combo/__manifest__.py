# -*- coding: utf-8 -*-
{
    'name': 'POS Selection Combo Pack',
    'summary': "Selection Combo pack is a combination of several products put together and allow to select from Products at a special price",
    'description': """
POS Selection Combo Pack.
===============================================
Selection Combo pack is a combination of several products put together and allow to select from Products at a special price.
combo pack is created to increase sales of the complementary products and to provide special offers to the customers.
With the help of POS Selection Combo Pack seller can sell products in packs as a combo product and allow facility to select products from it.
    """,

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Point of Sale',
    'version': '14.0.0.1.1',
    'depends': ['point_of_sale'],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_selection_combo_view.xml',
    ],
    'qweb': [
        'static/src/xml/Orderline.xml',
        'static/src/xml/WrappedProductNameLines.xml',
        'static/src/xml/ProductItem.xml',
        'static/src/xml/SelectionComboProductItem.xml',
        'static/src/xml/SelectionComboProductList.xml',
        'static/src/xml/SelectionComboOrderMenuList.xml',
        'static/src/xml/ProductSelectionPopup.xml',
    ],

    'license': "OPL-1",
    'price': 149,
    'currency': "EUR",

    "installable": True,

    'images': ['static/description/main.png'],
    'live_test_url': 'https://youtu.be/uf8oWiiO0M8',
}
