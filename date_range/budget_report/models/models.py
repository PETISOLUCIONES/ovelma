from odoo import models, fields, api


class PartnerInherited(models.Model):
    _inherit = "res.partner"
    _description = 'Partner Inherited'

    @api.model
    def create(self, vals_list):
        res = super(PartnerInherited, self).create(vals_list)

        self._cr.execute('SELECT DISTINCT x_studio_tamao_de_cliente \
                FROM res_partner WHERE x_studio_tamao_de_cliente IS NOT NULL;')

        res_partner_criteria_list = self._cr.fetchall()

        self._cr.execute('SELECT DISTINCT tamano_de_cliente \
                FROM budget_report WHERE tamano_de_cliente IS NOT NULL;')

        budget_report_criteria_list = self._cr.fetchall()

        res_partner_criteria_set = {criteria[0] for criteria in res_partner_criteria_list}
        budget_report_criteria_set = {criteria[0] for criteria in budget_report_criteria_list}

        if len(res_partner_criteria_set) > len(budget_report_criteria_set):
            tamano_de_cliente_records = res_partner_criteria_set - budget_report_criteria_set

            for tamano_de_cliente in tamano_de_cliente_records:
                product_object = self.env['product.template'].sudo().search(
                    [('sale_ok', '=', True), ('company_id', '!=', False)])
                for product_record in product_object:
                    self.env['budget.report'].sudo().create({
                        'product': product_record.name,
                        'product_id': product_record.id,
                        'criteria': tamano_de_cliente.split('-')[0],
                        'tamano_de_cliente': tamano_de_cliente,
                        'company': product_record.company_id.name
                    })

        return res

    def unlink(self):
        res = super(PartnerInherited, self).unlink()

        self._cr.execute('SELECT DISTINCT x_studio_tamao_de_cliente \
                FROM res_partner WHERE x_studio_tamao_de_cliente IS NOT NULL;')

        res_partner_criteria_list = self._cr.fetchall()

        self._cr.execute('SELECT DISTINCT tamano_de_cliente \
                FROM budget_report WHERE tamano_de_cliente IS NOT NULL;')

        budget_report_criteria_list = self._cr.fetchall()

        res_partner_criteria_set = {criteria[0] for criteria in set(res_partner_criteria_list)}
        budget_report_criteria_set = {criteria[0] for criteria in set(budget_report_criteria_list)}

        if len(res_partner_criteria_set) < len(budget_report_criteria_set):
            tamano_de_cliente_records = budget_report_criteria_set - res_partner_criteria_set

            for tamano_de_cliente in tamano_de_cliente_records:
                budget_report_object = self.env['budget.report'].sudo().search(
                    [('tamano_de_cliente', '=', tamano_de_cliente)])
                for budget_report_record in budget_report_object:
                    budget_report_record.unlink()

        return res


class ProductTemplateInherited(models.Model):
    _inherit = "product.template"
    _description = "Product Template Inherited"

    def record_sync(self, product_record, _action):
        if _action == 'create':
            self._cr.execute('SELECT DISTINCT x_studio_tamao_de_cliente \
                FROM res_partner WHERE x_studio_tamao_de_cliente IS NOT NULL;')

            criteria_object = self._cr.fetchall()

            for criteria_record in criteria_object:
                self.env['budget.report'].create({
                    'product': product_record.name,
                    'product_id': product_record.id,
                    'criteria': criteria_record[0].split('-')[0],
                    'tamano_de_cliente': criteria_record[0],
                    'company': product_record.company_id.name
                })

        elif _action == 'write':
            budget_report_object = self.env['budget.report'].sudo().search(
                [('product_id', '=', product_record.id)])

            for budget_report_record in budget_report_object:
                budget_report_record.write({
                    'product': product_record.name,
                    'company': product_record.company_id.name
                })
        else:
            budget_report_object = self.env['budget.report'].sudo().search(
                [('product_id', '=', product_record.id)])

            for budget_report_record in budget_report_object:
                budget_report_record.unlink()

    @api.model
    def create(self, vals_list):
        res = super(ProductTemplateInherited, self).create(vals_list)
        for record in res:
            self.record_sync(record, 'create')
        return res

    #@api.model
    def write(self, vals):
        res = super(ProductTemplateInherited, self).write(vals)
        for record in self:
            self.record_sync(record, 'write')
        return res

    def unlink(self):
        res = super(ProductTemplateInherited, self).unlink()
        for record in self:
            self.record_sync(record, 'unlink')
        return res


class BudgetReport(models.Model):
    _name = 'budget.report'
    _description = 'budget.report'

    criteria = fields.Char(string='Criteria')
    product = fields.Char(string='Product')
    product_id = fields.Char(string='Product ID')
    company = fields.Char(string='Company')
    tamano_de_cliente = fields.Char(string='Tamano De Cliente')

    january = fields.Integer(string='January')
    february = fields.Integer(string='February')
    march = fields.Integer(string='March')
    april = fields.Integer(string='April')
    may = fields.Integer(string='May')
    june = fields.Integer(string='June')
    july = fields.Integer(string='July')
    august = fields.Integer(string='August')
    september = fields.Integer(string='September')
    october = fields.Integer(string='October')
    november = fields.Integer(string='November')
    december = fields.Integer(string='December')

    @api.model
    def initialize_report(self):
        company_object = self.env['res.company'].sudo().search([])

        for company_record in company_object:
            product_object = self.env['product.template'].sudo().search([
                ('company_id', '=', company_record.id), ('sale_ok', '=', True)])

            self._cr.execute('SELECT DISTINCT x_studio_tamao_de_cliente \
                FROM res_partner WHERE x_studio_tamao_de_cliente IS NOT NULL;')

            criteria_object = self._cr.fetchall()
            for product_record in product_object:
                for criteria_record in criteria_object:
                    self.create({
                        'product': product_record.name,
                        'product_id': product_record.id,
                        'criteria': criteria_record[0].split('-')[0],
                        'tamano_de_cliente': criteria_record[0],
                        'company': company_record.name
                    })
