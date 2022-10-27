# -*- coding: utf-8 -*-

from functools import partial
from odoo import fields, models

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)

        process_line = partial(self.env['pos.order.line']._order_own_line_fields, add_own_line=True)

        order_lines = [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False

        new_order_line = []
        for order_line in order_lines:

            price_subtotal = 0
            price_subtotal_incl = 0

            if 'own_line' in order_line[2]:
                product = self.env['product.product'].search([('id', '=', order_line[2]['product_id'])])

                # print(order_line[2]['own_line'])
                # for line in order_line[2]['own_line']:
                #     line[2]['price_unit'] = line[2]['price']
                own_pro_list = [process_line(l) for l in order_line[2]['own_line']] if order_line[2]['own_line'] else False

                if own_pro_list:
                    for own in own_pro_list:

                        if product.include_price:
                            order_line[2]['price_subtotal'] -=own[2]['price_subtotal_incl']
                            order_line[2]['price_subtotal_incl'] -=own[2]['price_subtotal_incl']
                        # own[2]['price_unit'] = own[2]['price']
                        new_order_line.append(own)
            # order_line[2]['price_subtotal'] -= price_subtotal_incl
            # order_line[2]['price_subtotal_incl'] -= price_subtotal_incl

            new_order_line.append(order_line)


        # for line in new_order_line:
        #     if not 'price_unit' in line[2]:
        #         print(line[2])
        #         line[2]['price_unit'] = line[2]['price']
        if new_order_line:
            process_line = partial(self.env['pos.order.line']._order_line_fields)
            order_lines = [process_line(l) for l in new_order_line]
            res['lines'] = order_lines

        return res


class pos_order_line(models.Model):
    _inherit = "pos.order.line"

    is_selection_combo = fields.Boolean("Selection Combo Line")
    own_ids = fields.One2many("pos.order.line.own", 'orderline_id', "Extra Toppings")

    def _order_own_line_fields(self, line, session_id=None, add_own_line=False):
        own_line = []
        if line and 'own_line' in line[2] and add_own_line:
            own_line = line[2]['own_line']

        line = super(pos_order_line, self)._order_line_fields(line, session_id=session_id)

        if own_line:
            line[2]['own_line'] = own_line
        return line


class pos_order_line_own(models.Model):
    _name = "pos.order.line.own"
    _description = "POS Order Line own"

    orderline_id = fields.Many2one('pos.order.line', 'POS Line')
    product_id = fields.Many2one('product.product', 'Product')
    price = fields.Float('Item Price', required=True)
    qty = fields.Float('Quantity', default='1', required=True)
