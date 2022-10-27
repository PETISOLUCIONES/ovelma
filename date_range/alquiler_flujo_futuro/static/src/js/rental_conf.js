odoo.define('alquiler_flujo_futuro.RentalConfiguratorWidget', function (require) {
"use strict";
var core = require('web.core');
var ProductConfiguratorWidget = require('sale.product_configurator');

    ProductConfiguratorWidget.include({

        _defaultRentalData: function (data) {
           data = this._super.apply(this, data);
           if (this.recordData.price_month) {
                data.default_amount_month = this.recordData.price_month;
            }
            if (this.recordData.price_unit) {
                data.default_unit_price = this.recordData.price_unit;
            }
            return data;
        },

    });

    return ProductConfiguratorWidget;

});