odoo.define('pos_selection_combo.PosSelectionCombo', function (require) {
"use strict";

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const Models = require('point_of_sale.models');

    var utils = require('web.utils');
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    Models.load_fields("product.product",['is_selection_combo', 'product_topping_ids', 'include_price']);

    Models.load_models({
        model: 'product.selection.topping',
        fields: ['id', 'product_categ_id', 'multi_selection', 'product_ids', 'no_of_min_items', 'no_of_items', 'description'],
        loaded: function(self, result){
            self.topping_item_by_id = {};
            _.each(result, function(topping_item){
                self.topping_item_by_id[topping_item.id] = topping_item;
            })
        },
    });

    const SelectionComboProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                const self = this;
                const product = event.detail;
                var default_product_topping_id = false;
                if(product.is_selection_combo) {
                    const data = [];
                    _.each(product.product_topping_ids, function(product_topping_id){
                        const products = [];
                        const selected_product = self.env.pos.topping_item_by_id[product_topping_id];
                        _.each(selected_product.product_ids, function(product_id){
                            const item = self.env.pos.db.get_product_by_id(product_id);
                            if(item) products.push(item);
                        });
                        if (!default_product_topping_id) default_product_topping_id = selected_product.id
                        data.push({
                            'id': selected_product.id,
                            'category': selected_product.description,
                            'categ_id': selected_product.product_categ_id[0],
                            'products': products || [],
                            'multi_selection': selected_product.multi_selection,
                            'no_of_items': selected_product.no_of_items,
                            'no_of_min_items': selected_product.no_of_min_items,
                            'qty': selected_product.product_quantity,
                        });
                    });
                    this.env.pos.set('SelectionSelectedToppingId', default_product_topping_id);
                    await this.showPopup('ProductSelectionPopup', {
                        'data': data,
                        'main_product': product.id,
                        'main_product_name': product.display_name,
                        'main_product_price': product.lst_price,
                        'include_price': product.include_price,
                        'order_menu': []
                    });
                } else {
                    super._clickProduct(event);
                }
            }
        };

    Registries.Component.extend(ProductScreen, SelectionComboProductScreen);


    var _super_order_line = Models.Orderline.prototype;
    Models.Orderline = Models.Orderline.extend({
        init_from_JSON: function(json) {
            var self = this;
            _super_order_line.init_from_JSON.apply(this,arguments);
            this.own_data = this.own_data || json.own_data || [];
            this.order_menu = this.order_menu || json.order_menu || [];
            if (this.own_data && this.own_data.product_id == undefined) {
                var own_data = [];
                _.each(this.order_menu, function(order){
                    var products = [];
                    _.each(order.products, function(product){
                        own_data.push({
                            "product_id": self.pos.db.get_product_by_id(parseInt(product.product_id)),
                            'qty': product.qty,
                            'price': product.price,
                            'price_unit': product.price
                        });
                    });
                });
                this.own_data = own_data;
            }
        },

        set_own_data: function(own_data){
            this.own_data = own_data;
        },
        get_own_data: function(){
            return this.own_data;
        },
        set_order_menu: function(order_menu){
            this.order_menu = order_menu;
        },
        get_order_menu: function(){
            return this.order_menu;
        },
        compute_tax_fixed_price: function (taxes,price) {
            var order = this.order;
            if(order.fiscal_position) {
                // var taxes = this.get_taxes_with_id();
                var mapped_included_taxes = [];
                var new_included_taxes = [];
                var self = this;
                _(taxes).each(function(tax) {
                    var line_taxes = self._map_tax_fiscal_position(tax, order);
                    if (line_taxes.length && line_taxes[0].price_include){
                        new_included_taxes = new_included_taxes.concat(line_taxes);
                    }
                    if(tax.price_include && !_.contains(line_taxes, tax)){
                        mapped_included_taxes.push(tax);
                    }
                });

                if (mapped_included_taxes.length > 0) {
                    if (new_included_taxes.length > 0) {
                        var price_without_taxes = this.compute_all(mapped_included_taxes, price, 1, order.pos.currency.rounding, true).total_excluded
                        return this.compute_all(new_included_taxes, price_without_taxes, 1, order.pos.currency.rounding, false).total_included
                    }
                    else{
                        return this.compute_all(mapped_included_taxes, price, 1, order.pos.currency.rounding, true).total_excluded;
                    }
                }
            }
            return price;
        },
        get_taxes_with_id: function(taxes_ids){
            // var taxes_ids = this.get_product().taxes_id;
            var taxes = [];
            if (taxes_ids) {
              for (var i = 0; i < taxes_ids.length; i++) {
                  if (this.pos.taxes_by_id[taxes_ids[i]]) {
                      taxes.push(this.pos.taxes_by_id[taxes_ids[i]]);
                  }
              }
            }

            return taxes;
        },
        _compute_all_compo: function(tax, base_amount, quantity, price_exclude) {
            if(price_exclude === undefined)
                var price_include = tax.price_include;
            else
                var price_include = !price_exclude;
            if (tax.amount_type === 'fixed') {
                var sign_base_amount = Math.sign(base_amount) || 1;
                // Since base amount has been computed with quantity
                // we take the abs of quantity
                // Same logic as bb72dea98de4dae8f59e397f232a0636411d37ce
                return tax.amount * sign_base_amount * Math.abs(quantity);
            }
            if (tax.amount_type === 'percent' && !price_include){
                return base_amount * tax.amount / 100;
            }
            if (tax.amount_type === 'percent' && price_include){
                return base_amount - (base_amount / (1 + tax.amount / 100));
            }
            if (tax.amount_type === 'division' && !price_include) {
                return base_amount / (1 - tax.amount / 100) - base_amount;
            }
            if (tax.amount_type === 'division' && price_include) {
                return base_amount - (base_amount * (tax.amount / 100));
            }
            return false;
        },
        compute_all_compo: function(taxes, price_unit, quantity, currency_rounding, handle_price_include=true) {
            var self = this;

            // 1) Flatten the taxes.

            var _collect_taxes = function(taxes, all_taxes){
                taxes.sort(function (tax1, tax2) {
                    return tax1.sequence - tax2.sequence;
                });
                _(taxes).each(function(tax){
                    if(tax.amount_type === 'group')
                        all_taxes = _collect_taxes(tax.children_tax_ids, all_taxes);
                    else
                        all_taxes.push(tax);
                });
                return all_taxes;
            }
            var collect_taxes = function(taxes){
                return _collect_taxes(taxes, []);
            }

            taxes = collect_taxes(taxes);

            // 2) Deal with the rounding methods

            var round_tax = this.pos.company.tax_calculation_rounding_method != 'round_globally';

            var initial_currency_rounding = currency_rounding;
            if(!round_tax)
                currency_rounding = currency_rounding * 0.00001;

            // 3) Iterate the taxes in the reversed sequence order to retrieve the initial base of the computation.
            var recompute_base = function(base_amount, fixed_amount, percent_amount, division_amount){
                 return (base_amount - fixed_amount) / (1.0 + percent_amount / 100.0) * (100 - division_amount) / 100;
            }

            var base = round_pr(price_unit * quantity, initial_currency_rounding);

            var sign = 1;
            if(base < 0){
                base = -base;
                sign = -1;
            }

            var total_included_checkpoints = {};
            var i = taxes.length - 1;
            var store_included_tax_total = true;

            var incl_fixed_amount = 0.0;
            var incl_percent_amount = 0.0;
            var incl_division_amount = 0.0;

            var cached_tax_amounts = {};
            if (handle_price_include){
                _(taxes.reverse()).each(function(tax){
                    if(tax.include_base_amount){
                        base = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount);
                        incl_fixed_amount = 0.0;
                        incl_percent_amount = 0.0;
                        incl_division_amount = 0.0;
                        store_included_tax_total = true;
                    }
                    if(tax.price_include){
                        if(tax.amount_type === 'percent')
                            incl_percent_amount += tax.amount;
                        else if(tax.amount_type === 'division')
                            incl_division_amount += tax.amount;
                        else if(tax.amount_type === 'fixed')
                            incl_fixed_amount += Math.abs(quantity) * tax.amount
                        else{
                            var tax_amount = self._compute_all_compo(tax, base, quantity);
                            incl_fixed_amount += tax_amount;
                            cached_tax_amounts[i] = tax_amount;
                        }
                        if(store_included_tax_total){
                            total_included_checkpoints[i] = base;
                            store_included_tax_total = false;
                        }
                    }
                    i -= 1;
                });
            }

            var total_excluded = round_pr(recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount), initial_currency_rounding);
            var total_included = total_excluded;

            // 4) Iterate the taxes in the sequence order to fill missing base/amount values.

            base = total_excluded;

            var skip_checkpoint = false;

            var taxes_vals = [];
            i = 0;
            var cumulated_tax_included_amount = 0;
            _(taxes.reverse()).each(function(tax){
                if(!skip_checkpoint && tax.price_include && total_included_checkpoints[i] !== undefined){
                    var tax_amount = total_included_checkpoints[i] - (base + cumulated_tax_included_amount);
                    cumulated_tax_included_amount = 0;
                }else
                    var tax_amount = self._compute_all_compo(tax, base, quantity, true);

                tax_amount = round_pr(tax_amount, currency_rounding);

                if(tax.price_include && total_included_checkpoints[i] === undefined)
                    cumulated_tax_included_amount += tax_amount;

                taxes_vals.push({
                    'id': tax.id,
                    'name': tax.name,
                    'amount': sign * tax_amount,
                    'base': sign * round_pr(base, currency_rounding),
                });

                if(tax.include_base_amount){
                    base += tax_amount;
                    if(!tax.price_include)
                        skip_checkpoint = true;
                }

                total_included += tax_amount;
                i += 1;
            });

            return {
                'taxes': taxes_vals,
                'total_excluded': sign * round_pr(total_excluded, this.pos.currency.rounding),
                'total_included': sign * round_pr(total_included, this.pos.currency.rounding),
            }
        },
        export_as_JSON: function(){
            var self = this;
            var own_line = [];
            var total_price = 0.0;
            var json = _super_order_line.export_as_JSON.call(this,arguments);
            if(self.product.is_selection_combo && self.own_data) {
                _.each(self.own_data, function(item) {
                    var full_name = item.product_id.display_name;
                    if (item.product_id.description) {
                        full_name += ` (${item.product_id.description})`;
                    }
                    // var sub_total = item.price*self.get_quantity() * item.qty;

                    var tax = self.get_taxes_with_id(item.tax_id)
                    var item_price = self.compute_tax_fixed_price(tax,item.price_unit);
                    var computed_price = self.compute_all_compo(tax,item_price,self.get_quantity() * item.qty,self.pos.currency.rounding)


                    own_line.push([0, 0, {
                        'product_id': item.product_id.id,
                        'full_product_name': full_name,
                        'qty': self.get_quantity() * item.qty,
                        'tax_ids':[[6, false, _.map(tax, function(tax){ return tax.id; })]],
                        'price':item_price*self.get_quantity() * item.qty,
                        'price_unit':item_price,
                        'price_subtotal': computed_price.total_excluded,
                        'price_subtotal_incl': computed_price.total_included
                    }]);
                    total_price += item.price;
                });
            }
            if (this.product.is_selection_combo) {
                json.price_unit = total_price;
            }
            // json.price_unit = this.price;
            // var product = this.env.pos.db.get_product_by_id(this.main_product);
            json.price_unit = self.product.get_price(self.order.pricelist, 1);

            // json.price_subtotal = this.get_price_without_tax();
            // json.price_subtotal_incl = this.get_price_with_tax();
            json.is_selection_combo = this.product.is_selection_combo;
            json.own_line = this.product.is_selection_combo ? own_line : [];
            json.own_data = this.own_data;
            json.order_menu = this.order_menu;

            return json;
        },
        export_for_printing: function(){
            var json = _super_order_line.export_for_printing.call(this,arguments);
            json['order_menu'] = this.order_menu;
            json['is_selection_combo_product'] = this.get_product().is_selection_combo;
            json['name_arabic'] = this.get_product().name_arabic;
            console.log(json);
            return json;
        },
    });

    return SelectionComboProductScreen;
});
