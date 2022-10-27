odoo.define('pos_info_customer_peti', function(require){
    "use strict";

    var models = require('point_of_sale.models');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    models.load_fields("res.partner", ['firstname', 'other_name', 'lastname', 'other_lastname', 'xbirthday', 'vat_type', 'city_id', 'company_type', 'l10n_latam_identification_type_id', 'vat_vd', 'vat_num']);

    models.load_models({
        model:  'res.city',
        fields: ['name', 'state_id'],
        loaded: function(self,cities){
            self.cities = cities;
        },
    });
    models.load_models({
        model:  'l10n_latam.identification.type',
        fields: ['name', 'l10n_co_document_code'],
        loaded: function(self,identification_type){
            self.identification_type = identification_type;
        },
    });

const ClientDetailsEditNames = (ClientListScreen) =>
        class extends ClientListScreen {
        constructor() {
                super(...arguments);
                // trigger to close this screen (from being shown as tempScreen)
                useListener('discard', this.back);
            }

        editClient(){
            var self = this;
            super.editClient(...arguments);
			var contents = $('.client-details-contents');
			if (self.state.detailIsShown) {
			    contents.find('.client-address-states').on('change', function (ev) {
                    var $citySelection = contents.find('.client-address-cities');
                    var value = this.value;
                    $citySelection.empty()
                    $citySelection.append($("<option/>", {
                        value: '',
                        text: 'None',
                    }));
                    self.pos.cities.forEach(function (city) {
                        if (city.state_id[0] == value) {
                            $citySelection.append($("<option/>", {
                                value: city.id,
                                text: city.name
                            }));
                        }
                    });
                });
            }
        }
    };
    Registries.Component.extend(ClientListScreen, ClientDetailsEditNames);

    return ClientListScreen;

});