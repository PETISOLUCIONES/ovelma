odoo.define('alquiler_flujo_futuro.RentalConfiguratorFormController', function (require) {
"use strict";

var RentalConfiguratorFormController = require('sale_renting.RentalConfiguratorFormController');

    RentalConfiguratorFormController.include({

        _getRentalInfo: function (state) {
            var infos = this._super.apply(this, arguments);
            infos['price_month'] = state.amount_month;
            infos['months_rental'] = state.duration;
            return infos;
        }

    });
    return RentalConfiguratorFormController;
});