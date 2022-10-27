from odoo import models, fields, api

class ProductProductInherited(models.Model):

    _inherit = 'product.product'

    @api.model
    def create(self,vals):
        records = super(ProductProductInherited, self).create(vals)
        for rec in records:
            if rec.type == 'product':
                companies = self.env.cr.execute(f''' select distinct id from res_company ''')
                companies = self.env.cr.dictfetchall()
                for company in companies:
                    loc = self.env['stock.location'].sudo().search([('name','=', f'techneith_cero_{company["id"]}')])
                    if not loc:
                        loc = self.env['stock.location'].sudo().create({'name':f"techneith_cero_{company['id']}",'company_id':company["id"]})

                    if loc:
                        self.env['stock.quant'].sudo().create({'location_id':loc.id,'product_id':rec.id,'reserved_quantity':1,'is_dummy':True})
                    
        return records

class ProductLocationOnHand(models.Model):
    _name = "product.locationwise.onhand"
    _description = "Product on hand quantities location wise"

    quant_reference_id = fields.Many2one(comodel_name = 'stock.quant', string = 'Products',ondelete='cascade')
    product_id = fields.Many2one(comodel_name = 'product.product',related='quant_reference_id.product_id' ,string = 'Products',store=True)
    location_id = fields.Many2one(comodel_name = 'stock.location',related='quant_reference_id.location_id', string = 'Location',store=True)
    product_tmpl_id = fields.Many2one(comodel_name = 'product.template',related='product_id.product_tmpl_id' ,string = 'Products',store=True)
    company_id = fields.Many2one(comodel_name = 'res.company',related='quant_reference_id.company_id' ,string = 'company',store=True)
    onhand_qty = fields.Float(
        string='Onhand quantity',
        related='quant_reference_id.quantity',store=True)
    is_dummy = fields.Boolean(string='Cero quantity',related='quant_reference_id.is_dummy',store=True)

class ProductCostsCompanyWise(models.Model):
    
    _name = 'product.cost.companywise'

    property_reference_id = fields.Many2one(comodel_name = 'ir.property', string = 'Reference',ondelete='cascade')
    product_id = fields.Many2one(comodel_name = 'product.product',string = 'Products')
    custom_cost = fields.Float(string='Cost',related='property_reference_id.value_float',store=True)
    company_id = fields.Many2one(comodel_name = 'res.company',related = 'property_reference_id.company_id' ,string = 'Company',store=True)
    
    @api.model
    def create(self,vals):
        records = super(ProductCostsCompanyWise, self).create(vals)
        for rec in records:
            model_name,product_id = rec.property_reference_id.res_id.split(',')
            product = self.env['product.product'].sudo().search([('id','=',int(product_id))])
            if product:
                rec.product_id = product.id
        
        return records

class IrPropertyInherited(models.Model):

    _inherit = 'ir.property'

    @api.model
    def create(self,vals):
        records = super(IrPropertyInherited, self).create(vals)
        for rec in records:
            if rec.res_id and rec.res_id.split(',')[0] == 'product.product' and rec.name == 'standard_price':
                self.env['product.cost.companywise'].sudo().create({"property_reference_id":rec.id})
            
        return records

class ResCompanyInherited(models.Model):
    _inherit = 'res.company'

    @api.model
    def create(self,vals):
        records = super(ResCompanyInherited, self).create(vals)
        for rec in records:
            self.env['stock.location'].sudo().create({'name':f"techneith_cero_{rec.id}",'company_id':rec.id})
        return records
    
    def unlink(self):
        for rec in self:
            loc = self.env['stock.location'].sudo().search([('name','=', f'techneith_cero_{rec.id}')])
            for l in loc:
                l.unlink()
        
        records = super(ResCompanyInherited,self).unlink()
        return records

class StockQuantInherited(models.Model):

    _inherit = 'stock.quant'
    
    is_dummy = fields.Boolean(string='Cero quantity',default=False)

    @api.model
    def create(self,vals):
        records = super(StockQuantInherited, self).create(vals)
        for rec in records:
            if rec.is_dummy is False:
                quant = self.env['stock.quant'].sudo().search([('product_id','=', rec.product_id.id),('company_id','=',rec.company_id.id),('is_dummy','=',True)])
                for q in quant:
                    q.unlink()
            self.env['product.locationwise.onhand'].sudo().create({"quant_reference_id":rec.id})
        return records

    def unlink(self):
        for rec in self:
            quant = self.env['stock.quant'].sudo().search([('product_id','=', rec.product_id.id),('company_id','=',rec.company_id.id),('is_dummy','=',False)])
            if len(quant) == 1:
                loc = self.env['stock.location'].sudo().search([('name','=', f'techneith_cero_{rec.company_id.id}')])
                if not loc:
                    loc = self.env['stock.location'].sudo().create({'name':f"techneith_cero_{rec.company_id.id}",'company_id':rec.company_id.id})

                if loc:
                    self.env['stock.quant'].sudo().create({'location_id':loc.id,'product_id':rec.product_id.id,'reserved_quantity':1,'is_dummy':True})
                    

        records = super(StockQuantInherited,self).unlink()

        return records