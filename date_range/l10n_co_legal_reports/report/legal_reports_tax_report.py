# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning


class ReportTaxCertification(models.AbstractModel):
    _name = 'report.l10n_co_legal_reports.teplate_tax_certification'
    _description = "Colombian Tax Certification Report"

    @api.model
    def get_report_values(self, docids, data=None):

        docs = []
        partner_doc = {}

        tax_ids = data.get('tax_ids', False)
        partner_ids = data.get('partner_ids', False)
        company_id = data.get('company_id', False)
        date_from = data['wizard_values'].get('date_from', False)
        date_to = data['wizard_values'].get('date_to', False)
        if len(tax_ids) == 1:
            tax_ids = [tax_ids[0]]
        else:
            tax_ids = [x for x in tax_ids]

        for partner_id in partner_ids:
            SQL = """
                SELECT id FROM account_invoice
                    WHERE state IN ('open', 'paid') and
                        type LIKE 'in_%%' and
                        company_id=%(company_id)s and
                        partner_id=%(partner_id)s and
                        date between '%(date_from)s' and '%(date_to)s'
                """ % {
                'company_id': company_id,
                'partner_id': partner_id,
                'date_from': date_from,
                'date_to': date_to,
                'tax_ids': tax_ids,
            }

            self.env.cr.execute(SQL)
            invoice_ids = self.env.cr.fetchall()
            
            if len(invoice_ids) == 0:
                continue

            if len(invoice_ids) == 1:
                invoice_ids = [invoice_ids[0][0]]
            else:
                invoice_ids = [x[0] for x in invoice_ids]

            invoice_ids = self.env['account.invoice'].browse(invoice_ids)
            
            if not invoice_ids:
                raise ValidationError(
                    'No existen datos para "%s"' % (
                        self.env['res.partner'].browse(partner_id).name
                    )
                )

            lines = []
            for invoice in invoice_ids:
                for tax in invoice.tax_line_ids:
                    if tax.tax_id.id not in tax_ids:
                        continue
                    base = tax.base 
                    amount = tax.amount
                    if invoice.type.find('refund') > 0:
                        base *= -1
                        amount *= -1
                    not_lines_exist = True
                    for l in lines:
                        if l['tax_id'] == tax.tax_id.id:
                            l['base'] += base
                            l['amount'] += amount
                            not_lines_exist = False
                            break
                    if not_lines_exist:
                        lines.append({
                            'tax_id': tax.tax_id.id,
                            'tax_name': tax.name,
                            #'currency_id': move_line_id.currency_id.id,
                            'base': base,
                            'amount': amount,
                        })
                        

            partner_doc = {
                    'partner_id': self.env['res.partner'].browse(partner_id),
                    'lines': [],
            }
            if lines:
                partner_doc['lines'] = lines
                docs.append(partner_doc)
            else:
                raise ValidationError(
                    'No existen datos del informe para "%s"' % (
                        self.env['res.partner'].browse(partner_id).name
                    )
                )

        docs = [doc for doc in docs if doc['lines']]
        if not docs:
            raise ValidationError(_('No se encontraron datos para procesar.'))


        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
            'date_from': date_from,
            'date_to': date_to,
            'data': data['wizard_values'],
        }

