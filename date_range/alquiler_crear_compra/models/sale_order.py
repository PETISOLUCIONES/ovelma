from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        # self = self.with_context(sale_order_id=self.id)
        res = super(SaleOrder, self)._action_confirm()
        if res:
            self._create_purchase_order()
        return res

    def asignar_proveedor(self, product_id):
        partner = self.env.ref('alquiler_crear_compra.partner_not_assigned').id
        product = product_id.write({
            'seller_ids': [(0, 0, {
                'name': partner,
                'min_qty': 1,
                'price': 1})],
        })
        return product_id.seller_ids[0]


    def _create_purchase_order(self):
        for order in self:
            orders = {}
            for line in order.order_line:
                if line.is_rental and line.product_id.qty_available == 0:
                    supplier = line.product_id.with_company(order.company_id.id)._select_seller(
                        quantity=line.product_uom_qty, uom_id=line.product_uom)
                    if not supplier:
                        '''raise UserError(
                            _("No hay ningún proveedor asociado al producto %s. Defina un proveedor para este producto.") % (
                            line.product_id.display_name,))'''
                        supplier = self.asignar_proveedor(line.product_id)
                    else:
                        supplier = supplier[0]

                    partner_pricelist = supplier.name.property_product_pricelist

                    final_price = supplier.price

                    if supplier.name.id not in orders:
                        orders[supplier.name.id] = []

                    dict_line = {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_qty': line.product_uom_qty,
                        'order_id': line.order_id.id,
                        'product_uom': line.product_uom.id,
                        'taxes_id': line.product_id.supplier_taxes_id.ids,
                        'price_unit': final_price,
                        'sale_line_id': line.id
                    }

                    orders[supplier.name.id].append([0, 0, dict_line])
            for lines_order in orders:
                purchase = self.env['purchase.order'].create({
                    'partner_id': lines_order,
                    'date_order': str(order.date_order),
                    'order_line': orders[lines_order],
                    'origin': order.name,
                    'partner_ref': order.name,
                    #'dest_address_id': order.partner_shipping_id.id,
                })

        return True


'''class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        other_lines = self.filtered(lambda sol: not sol.is_rental)
        order_id = self._context.get('sale_order_id', False)
        order_lines = self.search([('order_id', '=', order_id)])
        super(SaleOrderLine, order_lines)._action_launch_stock_rule(previous_product_uom_qty)'''
