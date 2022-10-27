# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round



 

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_id = fields.Many2one('account.asset', string='Asset Linked', ondelete="set null", help="Asset created from this Journal Item", copy=False)

    


class AccountMove(models.Model):
    _inherit = 'account.move'

    negative_amount = fields.Boolean(string='is negative', store=True)
    asset_clasification = fields.Selection([('NIFF','NIFF'),
                        ('FISCAL','FISCAL'),
                        ('dismantlement','DESMANTELAMIENTO'),
                        ('NIFF_sale','NIFF Venta'),
                        ('NIFF_disp','NIFF Dispuesto'),
                        ('FISCAL_sale','FISCAL Venta'),
                        ('FISCAL_disp','FISCAL Dispuesto'),
                        ('NIFF_move','NIFF cambio modelo'),
                        ('FISCAL_move','FISCAL cambio modelo'),
                        ('valorizacion_niff','Valorizacion (+)'),
                        ('desvalorizacion_niff','Valorizacion (-)'),
                        ('desvalorizacion_fiscal','Valorizacion (-)'),
                        ('valorizacion_fiscal','Valorizacion (+)'),],string='Asset Type', default='FISCAL')
    # account_asset_second_id = fields.Many2one('account.asset', string='asset', related='asset_id')


    def _auto_create_asset(self):
        create_list = []
        invoice_list = []
        auto_validate = []
        for move in self:
            if not move.is_invoice():
                continue
            
            names = self.invoice_line_ids.mapped('name')

            for move_line in move.line_ids:
                if (
                    move_line.account_id
                    and (move_line.account_id.can_create_asset)
                    and move_line.account_id.create_asset != "no"
                    and not move.reversed_entry_id
                    and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                    and not move_line.asset_id
                    and move_line.name in names
                    and move_line.account_id.user_type_id not in (self.env.ref('account.data_account_type_current_liabilities'),self.env.ref('account.data_account_type_non_current_liabilities'))
                ):
                    if not move_line.name:
                        raise UserError(_('Journal Items of %s should have a label in order to generate an asset')%(move_line.account_id.display_name))
                        
                    asset_obj = self.env['account.asset'].search([('product_id','=',move_line.product_id.product_tmpl_id.id)])
                    if asset_obj:
                        raise UserError(_('An asset already exists with this product. (%s)')%(asset_obj[0].name))

                    vals = {
                        'name': move_line.name,
                        'partner_id': move_line.partner_id.id or False,
                        'company_id': move_line.company_id.id,
                        'currency_id': move_line.company_currency_id.id,
                        'original_move_line_ids': [(6, False, move_line.ids)],
                        'state': 'draft',
                        'acquisition_date': move.invoice_date,
                        'acquisition_date_niff': move.invoice_date,
                        'account_analytic_id': move_line.analytic_account_id.id or False,
                    }
                    model_id = move_line.account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                        })
                    # esta funcion asigna un producto al activo si se especifica en la factira, adelas si el producto
                    # tiene asignado un "asset_parent_id" le asigna automaticamente los campos del padre al nuevo activo
                    product = move_line.product_id
                    if product:
                        vals['name'] = '[' + move_line.product_id.default_code + '] ' + move_line.product_id.name
                        if product.asset_template_parent_id:
                            asset_parent = self.env['account.asset'].search([('product_id','=', product.asset_template_parent_id.id)], limit=1)
                            vals.update({
                                'asset_parent_id': asset_parent.id,
                                'product_id': product.product_tmpl_id.id,
                            })
                        else:
                            vals.update({
                                'product_id': product.product_tmpl_id.id,
                            })
                    auto_validate.append(move_line.account_id.create_asset == 'validate')
                    invoice_list.append(move)
                    create_list.append(vals)
                    

            if len(create_list) == 0:
                # total_taxes = {}
                # total_invoice = 0
                total_moves = []
                for move_line in move.invoice_line_ids:
                    
                    if (
                        move_line.account_id
                        and (move_line.account_id.can_create_asset)
                        and move_line.account_id.create_asset != "no"
                        and not move.reversed_entry_id
                        and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                        and not move_line.asset_id
                        and move_line.account_id.user_type_id in (self.env.ref('account.data_account_type_current_liabilities'),self.env.ref('account.data_account_type_non_current_liabilities'))
                    ):
                        total_moves.append(move_line.id)      
                        
                if len(total_moves) > 0:
                    vals = {
                        'name': 'Ingreso Diferido (' + move.name + ')',
                        'partner_id': move.partner_id.id or False,
                        'company_id': move.company_id.id,
                        'currency_id': move.company_currency_id.id,
                        'original_move_line_ids': [(6, False, total_moves)],
                        'state': 'draft',
                        'acquisition_date': move.invoice_date,
                        'acquisition_date_niff': move.invoice_date,
                    }
                    model_id = move_line.account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                        })
                    auto_validate.append(move_line.account_id.create_asset == 'validate')
                    invoice_list.append(move)                
                    create_list.append(vals)
        

        assets = self.env['account.asset'].create(create_list)

        for asset in assets:
            if not asset.asset_parent_id and asset.product_id.asset_template_parent_id and asset.asset_type == "purchase":
                asset.asset_parent_id = asset.product_id.asset_template_parent_id.id
                asset.onchange_asset_parent_id()
   
        for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):
            if 'model_id' in vals and not 'asset_parent_id' in vals:
                asset._onchange_model_id()
                asset._onchange_method_period()
                if validate:
                    asset.validate()
            if 'asset_parent_id' in vals:
                asset.onchange_asset_parent_id()
            if invoice:
                asset_name = {
                    'purchase': _('Asset'),
                    'sale': _('Deferred revenue'),
                    'expense': _('Deferred expense'),
                }[asset.asset_type]
                msg = _('%s created from invoice') % (asset_name)
                msg += ': <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>' % (invoice.id, invoice.name)
                asset.message_post(body=msg)
        return assets

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        move_vals = super(AccountMove, self)._prepare_move_for_asset_depreciation(vals)
        lines = move_vals.get('line_ids')
        asset = vals['asset_id']
        for line in lines:
            line[2]['partner_id'] = asset.partner_id.id if (asset.asset_type == 'expense' and asset.partner_id) else False
        move_vals['partner_id'] = asset.partner_id.id if (asset.asset_type == 'expense' and asset.partner_id) else False
        return move_vals


    #funcion para calcular lineas teniendo en cuenta los campos NIFF
    @api.model
    def _prepare_move_for_asset_depreciation_niff(self, vals):
        missing_fields = set(['asset_id', 'move_ref', 'amount', 'asset_remaining_value', 'asset_depreciated_value']) - set(vals)
        if missing_fields:
            raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
        asset = vals['asset_id']
        account_analytic_id = asset.account_analytic_id
        analytic_tag_ids = asset.analytic_tag_ids_niff
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(vals['amount'], company_currency, asset.company_id, depreciation_date)
        move_line_1 = {
            'name': asset.name,
            'account_id': asset.account_depreciation_id_niff.id,
            'partner_id': asset.partner_id.id if (asset.asset_type == 'expense' and asset.partner_id) else False,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id or False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * vals['amount'] or 0.0,
        }
        move_line_2 = {
            'name': asset.name,
            'account_id': asset.account_depreciation_expense_id_niff.id,
            'partner_id': asset.partner_id.id if (asset.asset_type == 'expense' and asset.partner_id) else False,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id or False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type in ('purchase', 'expense') else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and vals['amount'] or 0.0,
        }
        move_vals = {
            'ref': vals['move_ref'],
            'date': depreciation_date,
            'journal_id': asset.journal_id_niff.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'auto_post': asset.state == 'open',
            'partner_id': asset.partner_id.id if (asset.asset_type == 'expense' and asset.partner_id) else False,
            'asset_id': asset.id,
            'asset_remaining_value': vals['asset_remaining_value'],
            'asset_depreciated_value': vals['asset_depreciated_value'],
            'amount_total': amount,
            'name': '/',
            'asset_value_change': vals.get('asset_value_change', False),
            'type': 'entry',
            'currency_id': current_currency.id,
            'asset_clasification': 'NIFF',
        }
        return move_vals

    
    def _prepare_move_for_asset_depreciation_with_taxes(self, newlines, final_lines, asset):
        def get_line(line, vals, amount, account, tax):
            move_line = {
            'name': asset.name + ' (' + vals[0].name + ')',
            'account_id': account.id if account else vals[3].id,
            'partner_id': vals[6].id or False,
            'debit': amount if amount > 0 else 0,
            'credit': 0 if amount > 0 else -amount,
            'analytic_account_id': vals[4].id if vals[4] else False,
            'analytic_tag_ids': False,
            'tax_ids': tax.ids if tax else False,
            'recompute_tax_line': True if tax else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * vals['amount'] or 0.0,
            }
            return (0,0,move_line)

        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        line_count = 0
        for line in newlines:
            line_count += 1
            final_line_ids = []
            total_debit = 0
            total_credit = 0
            for vals in final_lines:
                amount = float_round(vals[1]/asset.method_number, precision_rounding=asset.currency_id.rounding) 
                if line_count == len(newlines):
                    amount = float_round(vals[5],precision_rounding=asset.currency_id.rounding)
                vals[5] -= amount
                final_line_ids.append(get_line(line, vals, amount, asset.account_depreciation_id, False))
                total_debit += final_line_ids[-1][2]['debit']
                final_line_ids.append(get_line(line, vals, -amount, False, asset.tax_ids))
                total_credit += final_line_ids[-1][2]['credit']
            debit_diference = line['amount_total'] - total_debit
            credit_diference = line['amount_total'] - total_credit
            if debit_diference != 0:
                final_line_ids[len(final_line_ids)-2][2]['debit'] = float_round(final_line_ids[len(final_line_ids)-2][2]['debit']+debit_diference,precision_rounding=asset.currency_id.rounding)
            if credit_diference != 0:
                final_line_ids[-1][2]['credit'] = float_round(final_line_ids[-1][2]['credit']+credit_diference,precision_rounding=asset.currency_id.rounding)
            line['line_ids'] = final_line_ids
        return newlines
        
    
    def _depreciate(self):
        # se reescribe la funcion ya que ahora toca tener en cuenta la calsificacion del movimiento, si es NIFF o FISCAL
        for move in self.filtered(lambda m: m.asset_id):
            asset = move.asset_id
            if asset.state in ('open', 'pause') or asset.both_paused or asset.niff_paused or asset.fiscal_paused:
                if asset.asset_type != 'sale':
                    asset.value_residual -= abs(move.amount_total if move.asset_clasification == 'FISCAL' and move.state == 'posted' else 0)
                    asset.value_residual_niff -= abs(move.amount_total if move.asset_clasification == 'NIFF' and move.state == 'posted' else 0)
                else:
                    objs = asset.original_move_line_ids.mapped('product_id') if asset.original_move_line_ids else asset
                    total = 0
                    for obj in objs:
                        for line in move.line_ids:
                            if line.name.find(obj.name) != -1:
                                total += line.debit
                    asset.value_residual -= total
                if len(asset.depreciation_move_ids.filtered(lambda move: move.state == 'draft')) == 0:
                    asset.write({'state':'close'})
            elif asset.state == 'close':
                asset.value_residual -= abs(move.amount_total if move.asset_clasification == 'FISCAL' and move.state == 'posted' else 0)
                asset.value_residual_niff -= abs(move.amount_total if move.asset_clasification == 'NIFF' and move.state == 'posted' else 0)
            else:
                raise UserError(_('You cannot post a depreciation on an asset in this state: %s') % dict(self.env['account.asset']._fields['state'].selection)[asset.state])


    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        super(AccountMove,self)._compute_amount()
        for move in self:
            if move.negative_amount:
                move.amount_total = -move.amount_total

               