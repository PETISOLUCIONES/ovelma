odoo.define('point_of_sale.ProductSelectionPopup', function(require) {
    'use strict';

    const { useState, useSubEnv } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    var utils = require('web.utils');
    var round_di = utils.round_decimals;
    var round_pr = utils.round_precision;

    class AddQtyPopup extends AbstractAwaitablePopup {

  		constructor() {
  			super(...arguments);
  		}

  		async apply_qty () {
  			let self = this;
  			let order = this.env.pos.get_order();
  			if(order){
  				// let orderlines = order.get_orderlines();
  				let selectedOrder = self.env.pos.get('selectedOrder');
  				// $('#apply_qty_code').click(function() {
  				let entered_qty = $("#entered_qty").val();
  				let partner_id;
  				let coupon_applied = true;
  				let used = false;
  				if (order.get_client() != null){
  					partner_id = order.get_client();
  				}
          self.trigger('close-popup');
  				// let total_amount = selectedOrder.get_total_without_tax();
  				// await self.rpc({
  				// 	model: 'pos.gift.coupon',
  				// 	method: 'search_coupon',
  				// 	args: [1, entered_code],
          //
  				// }).then(function(output) {
  				// 	if(output.length > 0)
  				// 	{
          //
          //   }else { //Invalid Coupon Code
  				// 		Gui.showPopup('ErrorPopup', {
  				// 			'title': self.env._t('Invalid Code !!!'),
  				// 			'body': self.env._t("Voucher Code Entered by you is Invalid. Enter Valid Code..."),
  				// 		});
  				// 	}
  				// });
  			}
  		}
  	};

  	AddQtyPopup.template = 'AddQtyPopup';

  	Registries.Component.add(AddQtyPopup);



    class ProductSelectionPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener('click-combo-product', this._clickProduct);
            useListener('remove-combo-product', this._removeProduct);
            useListener('switch-category', this._switchCategory);
            this.data = this.props.data;
            this.main_product = this.props.main_product;
            this.main_product_name = this.props.main_product_name;
            this.main_product_price = this.props.main_product_price;
            this.pricelist = this.currentOrder.pricelist;
            this.popup = useState({ isRemoved: false});
            useSubEnv({ order_menu: this.props.order_menu || [] });
        }
        mounted() {
            this.env.pos.on('change:SelectionSelectedToppingId', this.render, this);
        }
        willUnmount() {
            this.env.pos.off('change:SelectionSelectedToppingId', null, this);
        }
        get SelectionSelectedToppingId() {
            return this.env.pos.get('SelectionSelectedToppingId');
        }
        get productsToDisplay() {
            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId]
            var list = [];
            if (topping_data) {
                var product_ids = topping_data.product_ids;
                if (product_ids) {
                    for (var i = 0; i < product_ids.length; i++) {
                        list.push(this.env.pos.db.get_product_by_id(product_ids[i]));
                    }
                }
            }
            return list;
        }
        get OrderMenuToDisplay() {
            return this.env.order_menu;
        }
        get TotalPriceToDisplay() {
            var total_price = 0.0;
            _.each(this.env.order_menu, function(order){
                _.each(order.products, function(product){
                    total_price += product.price;
                });
            });
            return total_price.toFixed(2);
        }
        async _clickProduct(event) {
          var self = this;
            if (this.popup.isRemoved) {
                this.popup.isRemoved = false;
                return
            }
            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId];
            if (!topping_data) return;
            const category = topping_data.product_categ_id[0];
            const product = event.detail.product;
            const description = topping_data.description;
            const multi_selection = topping_data.multi_selection;
            var allow = true;
            var order_menu = this.props.order_menu || [];

            if(!topping_data.no_of_items && multi_selection){
                return
            }

            var item = _.where(order_menu, {'toppingId': topping_data.id})
            if(item && item.length > 0){
                item = item[0];
                var item_products = item.products;

                if(item_products.length > 0 && multi_selection == false){
                    alert("You can select only one item.");
                    allow = false;
                    return
                } else {
                    var total_items = 0;
                    _.each(item_products, function(product){
                        total_items += product.qty;
                    });
                    if(item_products.length > 0 && total_items >= topping_data.no_of_items){
                        alert("You can only select "+ topping_data.no_of_items + " item from "+ topping_data.description);
                        return
                    }
                }
            }

            for(var i=0; i < order_menu.length; i++){
                if(topping_data.id == order_menu[i].toppingId){
                    var exist_product = _.find(order_menu[i].products, function(p) { return p.product_id === product.id});
                    if(exist_product) {
                        exist_product['qty'] = exist_product.qty + 1;
                        exist_product['price'] = exist_product.qty * exist_product['price_unit'];
                        // exist_product['price'] = exist_product.qty * product.get_price(this.pricelist,1);
                        allow = false;
                    } else {
                        order_menu[i].products.push({
                                'product_id': product.id,
                                'name_arabic': product.name_arabic,
                                'product_name': product.display_name,
                                'price': product.get_price(this.pricelist,1),
                                'price_unit': product.get_price(this.pricelist,1),
                                'qty': 1,
                                'tax_id': product.taxes_id,

                            });
                    }
                    allow = false;
                }
                if(order_menu[i].products.length <= 0){
                    order_menu.splice(i, 1);
                }
            }
            if(allow){
              // self.showPopup('AddQtyPopup', {});

              // var order = this.env.pos.get_order().get_selected_orderline();
              // var tax = order.get_taxes_with_id(product.taxes_id);
              // var item_price = order.compute_tax_fixed_price(tax,product.get_price(this.pricelist,1));
              // var computed_price = order.compute_all_compo(tax,item_price,1,this.env.pos.currency.rounding);

              order_menu.push({
                      'toppingId': topping_data.id,
                      'categoryName': description,
                      'include_price': this.props.include_price,
                      'products': [{
                          'product_id':product.id,
                          'name_arabic': product.name_arabic,
                          'product_name': product.display_name,
                          'price': product.get_price(this.pricelist, 1),
                          'price_unit': product.get_price(this.pricelist, 1),
                          'qty': 1,
                          'tax_id': product.taxes_id,
                          // 'price_unit':item_price,
                          // 'price_subtotal': computed_price.total_excluded,
                          // 'price_subtotal_incl': computed_price.total_included
                      }]
                  });
            }

            this.env.order_menu = order_menu;
            this.render();
        }
        async _removeProduct(event) {
            this.popup.isRemoved = true;

            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId];
            const product = event.detail.product;
            _.each(this.env.order_menu, function(order_menu){
                if(topping_data.id == order_menu.toppingId){
                    order_menu['products'] = _.reject(order_menu.products, function(p){ return p.product_id === product.id });
                }
            });

            var order_menu = _.reject(this.env.order_menu, function(order_menu){ return order_menu.products < 1});
            this.env.order_menu = order_menu;
            this.render();


        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        update_order_line(product, total_price) {
            this.currentOrder.add_product(product, {'price': product.get_price(this.pricelist, 1) + total_price});
            this.currentOrder.selected_orderline.price_manually_set = true;
        }
        get_taxes_with_id(taxes_ids){
            // var taxes_ids = this.get_product().taxes_id;
            var taxes = [];
            if (taxes_ids) {
              for (var i = 0; i < taxes_ids.length; i++) {
                  if (this.env.pos.taxes_by_id[taxes_ids[i]]) {
                      taxes.push(this.env.pos.taxes_by_id[taxes_ids[i]]);
                  }
              }
            }

            return taxes;
        }
        _compute_all(tax, base_amount, quantity, price_exclude) {
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
        }
        compute_all_compo(taxes, price_unit, quantity, currency_rounding, handle_price_include=true) {
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

            var round_tax = this.env.pos.company.tax_calculation_rounding_method != 'round_globally';

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
                            var tax_amount = self._compute_all(tax, base, quantity);
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
                    var tax_amount = self._compute_all(tax, base, quantity, true);

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
                'total_excluded': sign * round_pr(total_excluded, this.env.pos.currency.rounding),
                'total_included': sign * round_pr(total_included, this.env.pos.currency.rounding),
            }
        }
        async confirm() {
            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId];
            if (!topping_data) return;
            const multi_selection = topping_data.multi_selection;
            const self = this;

            var own_data = [];
            var selection = [];
            var total_price = 0.0;
            var required_sub_item = false;

            for(var i=0; i < this.data.length; i++){
                if (this.data[i].no_of_min_items != 0){
                    required_sub_item = true;
                    break;
                }
            }
            if (this.env.order_menu.length == 0 && required_sub_item) {
                alert("You can not confirm without select any item of min qty > 0 lines!");
                return
            } else {
                for(var i=0; i < this.data.length; i++){
                    if (this.data[i].no_of_min_items != 0){
                        var min_items = 0;
                        for(var j=0; j < this.env.order_menu.length; j++){
                            _.each(this.env.order_menu[j]['products'], function(product){
                                if (self.env.order_menu[j]['toppingId'] == self.data[i]['id']) {
                                    min_items += product.qty;
                                }
                            });
                        }
                        if(this.data[i].no_of_min_items > min_items){
                            alert("You Must Have to Select " + this.data[i].no_of_min_items + " item from " + this.data[i].category);
                            return
                        }
                    }
                }
            }

            for(var i=0; i < this.env.order_menu.length; i++){
                const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId];
                var total_items = 0;
                _.each(this.env.order_menu[i]['products'], function(product){
                    total_items += product.qty;
                });
                if(total_items < topping_data.no_of_min_items && multi_selection != false){
                    alert("You Must Have to Select " + topping_data.no_of_min_items + " item from " + topping_data.category);
                    return
                }

                for(var j=0; j < this.env.order_menu[i].products.length; j++) {
                    var product_id = this.env.order_menu[i].products[j].product_id;

                    var prod = this.env.pos.db.get_product_by_id(parseInt(product_id));

                    var tax = this.get_taxes_with_id(prod.taxes_id)

                    var computed_price = this.compute_all_compo(tax,this.env.order_menu[i].products[j].price_unit,this.env.order_menu[i].products[j].qty,this.env.pos.currency.rounding)
                    own_data.push({
                        "product_id": this.env.pos.db.get_product_by_id(parseInt(product_id)),
                        'qty': this.env.order_menu[i].products[j].qty,
                        'price': this.env.order_menu[i].products[j].price,
                        'tax_id': prod.taxes_id,
                        'price_unit':this.env.order_menu[i].products[j].price_unit,
                        'price_subtotal': computed_price.total_excluded,
                        'price_subtotal_incl': computed_price.total_included
                    });
                    // var pp = this.currentOrder.
                    if (this.env.order_menu[i].include_price) {
                      total_price += computed_price.total_included;
                        // total_price += this.env.order_menu[i].products[j].price;
                    }
                }
            }
            var product = this.env.pos.db.get_product_by_id(this.main_product);

            this.update_order_line(product, total_price);

            this.currentOrder.selected_orderline.set_own_data(own_data);
            this.currentOrder.selected_orderline.set_order_menu(this.env.order_menu);
            this.currentOrder.selected_orderline.set_selected();
            super.confirm();
        }
        _switchCategory(event) {
            this.env.pos.set('SelectionSelectedToppingId', event.detail);
        }

    }

    ProductSelectionPopup.template = 'ProductSelectionPopup';
    ProductSelectionPopup.defaultProps = {
        confirmText: 'Confirm',
        cancelText: 'Cancel',
    };

    Registries.Component.add(ProductSelectionPopup);

    return ProductSelectionPopup;
});
