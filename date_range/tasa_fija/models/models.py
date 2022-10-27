from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tasa_fija = fields.Float('Tasa fija de cambio', digits=(16, 6))


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_account_change_currency(self):
        partner = self.partner_id
        if partner:
            if partner.partner_currency_id and partner.tasa_fija:
                self.custom_rate = partner.tasa_fija
        super(AccountMove, self).action_account_change_currency()


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def _prepare_invoice_line(self, line, fiscal_position, date_start=False, date_stop=False):
        res = super(SaleSubscription, self)._prepare_invoice_line(line, fiscal_position, date_start=date_start,
                                                                  date_stop=date_stop)
        partner = self.partner_id
        currency = self.pricelist_id.currency_id
        company = self.env.user.company_id
        if self.invoice_currency and partner.tasa_fija and self.currency_id and currency != company.currency_id:
            context = {"custom_rate": partner.tasa_fija, "to_currency": company.currency_id}
            original_currency = currency.with_context(**context)
            res.update({
                'price_unit': original_currency._convert(line.price_unit, company.currency_id, company, self.recurring_next_date or fields.Date.today()),
            })
        return res
