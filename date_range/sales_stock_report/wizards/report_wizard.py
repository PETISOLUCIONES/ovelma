from odoo import fields, api, models, _
from calendar import monthrange


class StockReportWizard(models.TransientModel):
    _name = 'stock.report.wizard'
    _description = 'Stock Report Wizard'

    location_ids = fields.Many2many('stock.location', string='Locations', required=True)
    
    @api.model
    def default_get(self, fields):
        res = super(StockReportWizard, self).default_get(fields)
        location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        res.update({
            'location_ids': [(6, 0, location_ids.ids)],
        })
        return res
    
    def open_report(self):
        self.ensure_one()
        self._compute_stock_report_by_location()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot,tree',
            'name': _('Stock Report by Location'),
            'context': {'group_by_no_leaf': 1, 'group_by': []},
            'res_model': 'sale.stock.report',
            'domain': [('wiz_id', '=', self.id)],
        }
        return action

    def _compute_stock_report_by_location(self):
        self.ensure_one()
        recs = []
        now = fields.Datetime.now()
        start_datetime = now.replace(day=1).strftime("%Y-%m-%d 00:00:00")
        customer_location_id = self.env['stock.location'].search([('usage', '=', 'customer')])
        end_datetime = now
        move_obj = self.env['stock.move.line']
        stock_quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        stock_report_obj = self.env['sale.stock.report']
        for loc in self.location_ids:
            quant_groups = stock_quant_obj.read_group(
                [('location_id', 'child_of', [loc.id])],
                ['quantity', 'product_id'],
                ['product_id'])
            mapping = dict(
                [(quant_group['product_id'][0],
                  quant_group['quantity'])
                 for quant_group in quant_groups]
            )
            stock_move_groups = move_obj.read_group([   
                    ('location_id', 'child_of', [loc.id]),
                    ('date', '>=', start_datetime),
                    ('date', '<=', end_datetime),
                    ('state', '=', 'done'),
                    ('location_dest_id', 'in', customer_location_id.ids),
#                     ('sale_line_id', '!=', False)
                ],
                ['qty_done', 'product_id'],
                ['product_id'])
            stock_mapping = dict(
                [(stock_move_group['product_id'][0],
                  stock_move_group['qty_done'])
                 for stock_move_group in stock_move_groups]
            )
            products = product_obj.search(
                [('type', '=', 'product')])
            for product in products:
                r = stock_report_obj.create({
                    'product_id': product.id,
                    'product_category_id': product.categ_id.id,
                    'uom_id': product.uom_id.id,
                    'quantity': mapping.get(product.id, 0.0),
                    'sale_quantity': stock_mapping.get(product.id, 0.0),
                    'location_id': loc.id,
                    'wiz_id': self.id,
                    'provider_name': product.product_tmpl_id.x_studio_proveedor
                })
                recs.append(r.id)
        return recs


class SaleStockReport(models.TransientModel):
    _name = 'sale.stock.report'
    _description = 'Stock Report By Location'
    
    
    wiz_id = fields.Many2one('stock.report.wizard')
    product_id = fields.Many2one('product.product', required=True)
    provider_name = fields.Char(string='Proveedor')
    product_category_id = fields.Many2one('product.category', string='Product Category')
    location_id = fields.Many2one('stock.location', required=True)
    quantity = fields.Float(string="Qty On Hand")
    sale_quantity = fields.Float(string="Sale Qty")
    uom_id = fields.Many2one('uom.uom', string='Product UoM')
    default_code = fields.Char(string='Internal Reference')
