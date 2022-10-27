from odoo import models, fields, api, _

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.depends('product_id', 'location_id')
    def _location_stock_compute(self):
        for rec in self:
            inventory_quantity = 0
            if rec.product_id and rec.location_id:
                quant_groups = self.env['stock.quant'].read_group(
                    [('location_id', 'child_of', [rec.location_id.id]), ('product_id', '=', rec.product_id.id)],
                    ['quantity', 'product_id'],
                    ['product_id'])
                mapping = dict(
                    [(quant_group['product_id'][0],
                      quant_group['quantity'])
                     for quant_group in quant_groups]
                )
                inventory_quantity = mapping.get(rec.product_id.id, 0.0)
            rec.location_stock = inventory_quantity


    @api.depends('product_id', 'location_dest_id')
    def _location_dest_stock_compute(self):
        for rec in self:
            inventory_quantity = 0
            if rec.product_id and rec.location_dest_id:
                quant_groups = self.env['stock.quant'].read_group(
                    [('location_id', 'child_of', [rec.location_dest_id.id]), ('product_id', '=', rec.product_id.id)],
                    ['quantity', 'product_id'],
                    ['product_id'])
                mapping = dict(
                    [(quant_group['product_id'][0],
                      quant_group['quantity'])
                     for quant_group in quant_groups]
                )
                inventory_quantity = mapping.get(rec.product_id.id, 0.0)
            rec.location_dest_stock = inventory_quantity
    
    location_stock = fields.Float(string='Source Stock', compute='_location_stock_compute', store=False)
    location_dest_stock = fields.Float(string='Destination Stock', compute='_location_dest_stock_compute', store=False)
