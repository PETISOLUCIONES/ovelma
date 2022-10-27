# -*- coding: utf-8 -*-
from odoo.http import Controller, route, request
from werkzeug.utils import redirect


class BudgetReport(Controller):

    @route('/budget-report/', methods=['GET', 'POST'], type='http', auth="public", website=True, csrf=False)
    def budget_report_list(self, **kw):

        if not request.session.get('company_filter'):
            request.session['company_filter'] = request.env['res.company'].sudo().search([])[0].name

        budget_report_object = request.env['budget.report'].sudo()

        sortby = kw.get('sortby')
        sortby = sortby.replace('_', ' ') if sortby else "criteria asc"

        # Getting the product name from the request as product_filter
        product_fitler = kw.get('product_fitler')
        product_fitler = product_fitler.split('--') if product_fitler else []



        criteria_fitler = kw.get('criteria_fitler')
        criteria_fitler = criteria_fitler.split('--') if criteria_fitler else []


        # use product_id instead of product by the the product name
        if product_fitler and criteria_fitler:
            domains = [('product_id', 'in', product_fitler), ('criteria', 'in', criteria_fitler),
                       ('company', '=', request.session.get('company_filter'))]
        elif criteria_fitler:
            domains = [('criteria', 'in', criteria_fitler),
                       ('company', '=', request.session.get('company_filter'))]
        elif product_fitler:
            domains = [('product_id', 'in', product_fitler),
                       ('company', '=', request.session.get('company_filter'))]
        else:
            domains = [('company', '=', request.session.get('company_filter'))]

        filter_budget_report_object = budget_report_object.search(
            [('company', '=', request.session.get('company_filter'))])
        print(sortby)
        budget_report_object = budget_report_object.search(domains, order=sortby)

        print(budget_report_object)

        if 1000 < len(budget_report_object):
            budget_report_object = budget_report_object[:1000]

        #pass the product_id and product name for options field in Template.xml
        data = {
            'budget_report_object': budget_report_object,
            'unique_criteria_filter_list': sorted(set([record.criteria for record in filter_budget_report_object])),
            'unique_product_filter_list': sorted(set([(record.product, record.product_id) for record in filter_budget_report_object]))
        }

        return request.render('budget_report.budget_report_template', data)

    @route('/budget-report-value-set/', methods=['POST'], type='http', auth="public", website=True, csrf=False)
    def budget_report_value_set(self, **kw):

        budget_report_object = request.env['budget.report'].sudo()

        months_dict = {
            'Jan': 'january', 'Feb': 'february', 'Mar': 'march', 'Apr': 'april',
            'May': 'may', 'Jun': 'june', 'Jul': 'july', 'Aug': 'august',
            'Sep': 'september', 'Oct': 'october', 'Nov': 'november', 'Dec': 'december'
        }

        month_name = kw.get('month_input')
        month_value = kw.get('month_value')

        params = kw.get('params')
        product_fitler, criteria_fitler, sortby = params.replace('%20', ' ').split('&')

        # Getting the product name from the request as product_filter same as above
        product_fitler = product_fitler.split('=')[1].split('--')
        product_fitler = product_fitler if product_fitler != [''] else []

        criteria_fitler = criteria_fitler.split('=')[1].split('--')
        criteria_fitler = criteria_fitler if criteria_fitler != [''] else []

        #Pass product_id instead of product in the domain
        if product_fitler and criteria_fitler:
            domains = [('product_id', 'in', product_fitler), ('criteria', 'in', criteria_fitler),
                       ('company', '=', request.session.get('company_filter'))]
        elif criteria_fitler:
            domains = [('criteria', 'in', criteria_fitler),
                       ('company', '=', request.session.get('company_filter'))]
        elif product_fitler:
            domains = [('product_id', 'in', product_fitler),
                       ('company', '=', request.session.get('company_filter'))]
        else:
            domains = [('company', '=', request.session.get('company_filter'))]

        budget_report_object = budget_report_object.search(domains)



        for budget_report_record in budget_report_object:
            print(budget_report_record)

            budget_report_record.write({months_dict[month_name]: month_value})

        return redirect(f"/budget-report/?{params.replace('%20', ' ')}")

    @route('/budget-report-company-set/', methods=['POST'], type='http', auth="public", website=True, csrf=False)
    def budget_report_company_set(self, **kw):

        request.session['company_filter'] = kw.get('company_input')

        return redirect('/budget-report/')
