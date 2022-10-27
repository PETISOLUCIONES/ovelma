odoo.define('point_of_sale.SelectionComboOrderMenuList', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    // const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { useState, useSubEnv } = owl.hooks;


    class SelectionComboOrderMenuList extends PosComponent {

      constructor() {
        super(...arguments);
        useListener('click-change-qty', this._change_qty);

        useSubEnv({ order_menu: this.props.OrderMenu || [] });
      }





      async _change_qty(event) {
        var self = this;

        const product = event.detail.product;
        const category = event.detail.categ;
        const topping_data = this.env.pos.topping_item_by_id[category.toppingId];
        var order_menu = this.props.OrderMenu || [];

        var input = document.getElementById("input_"+product.product_id);

        if (input == null) {
          var prod_ids = []

          _.each(order_menu, function(order){
            _.each(order.products, function(product){
              prod_ids.push("input_"+product.product_id)
            });
          });

          prod_ids = prod_ids.filter(product_id => product_id != "input_"+product.product_id )
          var product_qty_elements = document.getElementsByClassName('product_qty');
          // var product_qty_element = product_qty_elements.filter(element_id => prod_ids.includes(element_id.firstElementChild.id) )
          _.each(product_qty_elements, function(product_qty){
            if(!prod_ids.includes(product_qty.firstElementChild.id)){
              product_qty.firstElementChild.setAttribute("id", "input_"+product.product_id);
            }
          });
          input = document.getElementById("input_"+product.product_id);

        }


        var entered_qty = parseInt(input.value);
        // var entered_qty = 5;

        var item = _.where(order_menu, {'toppingId': topping_data.id})
        if(item && item.length > 0){
            item = item[0];
            // var item_products = item.products;
            // var item_products = _.where(item.products, {'product_id': product.product_id})
            var item_products = (item.products).filter(prod => prod.product_id != product.product_id )

            var total_items = 0;
            _.each(item_products, function(product){
                total_items += product.qty;
            });
            total_items += entered_qty;

            if(total_items > topping_data.no_of_items){
                alert("You can only select "+ topping_data.no_of_items + " item from "+ topping_data.description);
                return
            }

        }
        for(var i=0; i < order_menu.length; i++){
            if(topping_data.id == order_menu[i].toppingId){
                var exist_product = _.find(order_menu[i].products, function(p) { return p.product_id === product.product_id});
                if(exist_product) {
                    exist_product['qty'] = entered_qty;
                    exist_product['price'] = entered_qty * exist_product['price_unit'];
                }
            }

            if(order_menu[i].products.length <= 0){
                order_menu.splice(i, 1);
            }

        }
        // var total_price = document.getElementsByClassName('total-price');
        // console.log(total_price);
        // console.log(total_price[0].innerHTML);
        // total_price[0].innerHTML = "50";

        this.env.order_menu = order_menu;
        this.render();


      }



    }
    SelectionComboOrderMenuList.template = 'SelectionComboOrderMenuList';

    Registries.Component.add(SelectionComboOrderMenuList);

    return SelectionComboOrderMenuList;
});
