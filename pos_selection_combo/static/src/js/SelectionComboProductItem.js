odoo.define('point_of_sale.SelectionComboProductItem', function(require) {
    'use strict';

    const ProductItem = require('point_of_sale.ProductItem');
    const Registries = require('point_of_sale.Registries');

    class SelectionComboProductItem extends ProductItem {
        get highlight() {
            const product = this.props.product;
            var is_highlight = '';
            for(var i=0; i < this.env.order_menu.length; i++){
                if(this.env.pos.get('SelectionSelectedToppingId') == this.env.order_menu[i].toppingId){
                    if (this.env.order_menu[i].products.findIndex(p => p.product_id == product.id) > -1) {
                        is_highlight = 'green_border';
                        break;
                    }
                }
            }
            return is_highlight;
        }
    }
    SelectionComboProductItem.template = 'SelectionComboProductItem';

    Registries.Component.add(SelectionComboProductItem);

    return SelectionComboProductItem;
});