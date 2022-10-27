
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    asset_template_parent_id = fields.Many2one('product.template', string='Producto del activo principal')
    childs = fields.Integer(string='# Hijos de este producto', default=0)

    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        for vals in vals_list:
            if vals.get('asset_template_parent_id'):
                product_obj = self.env['product.template'].browse(vals.get('asset_template_parent_id'))
                if product_obj:
                    product_obj.childs += 1
                    default_code = product_obj.default_code + '-' + str(product_obj.childs)
                    vals['default_code'] = default_code 
                    # vals['categ_id'] = product_obj.categ_id 
        templates = super(ProductTemplate, self).create(vals_list)
        return templates