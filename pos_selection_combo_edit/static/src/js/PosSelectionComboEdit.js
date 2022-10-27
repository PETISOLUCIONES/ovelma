odoo.define('pos_selection_combo_edit.PosSelectionComboEdit', function (require) {
"use strict";

    const Models = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const ProductSelectionPopup = require('point_of_sale.ProductSelectionPopup');

    Models.load_fields("product.product", ['is_editable_items']);

    const SelectionComboPosSelectionCombo = (ProductSelectionPopup) =>
        class extends ProductSelectionPopup {
            constructor() {
                super(...arguments);
                this.is_editable = this.props.is_editable || false;
                this.selected_orderline = this.props.selected_orderline || false;
                if(this.is_editable) {
                    this.selected_order_menu = JSON.parse(JSON.stringify(this.selected_orderline.order_menu));
                }
            }
            update_order_line(product, total_price) {
                if(this.is_editable) {
                    this.selected_orderline.set_unit_price(product.get_price(this.pricelist,1) + total_price);
                    this.currentOrder.select_orderline(this.selected_orderline);
                } else {
                    super.update_order_line(product, total_price);
                }
            }
            cancel() {
                if(this.is_editable) {
                    this.selected_orderline.order_menu = this.selected_order_menu;
                }
                super.cancel();
            }
        };

    Registries.Component.extend(ProductSelectionPopup, SelectionComboPosSelectionCombo);

    return SelectionComboPosSelectionCombo;
});
