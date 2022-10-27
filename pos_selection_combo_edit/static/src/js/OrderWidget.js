odoo.define('pos_selection_combo_edit.SelectionComboOrderWidget', function (require) {
"use strict";

    const OrderWidget = require('point_of_sale.OrderWidget');
    const Registries = require('point_of_sale.Registries');

    const SelectionComboOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            _selectLine(event) {
                super._selectLine(event);
                const self = this;
                const orderline = event.detail.orderline;
                const product = orderline.product;
                var default_product_topping_id = false;
                if(orderline && product.is_editable_items) {
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
                    this.showPopup('ProductSelectionPopup', {
                        'data': data,
                        'main_product': product.id,
                        'main_product_name': product.display_name,
                        'main_product_price': orderline.get_display_price(),
                        'include_price': product.include_price,
                        'is_editable': product.is_editable_items,
                        'order_menu': orderline.order_menu,
                        'selected_orderline': orderline,
                    });
                }
            }
        };

    Registries.Component.extend(OrderWidget, SelectionComboOrderWidget);

    return SelectionComboOrderWidget;
});
