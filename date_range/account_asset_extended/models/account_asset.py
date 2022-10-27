import calendar
from dateutil.relativedelta import relativedelta
from math import copysign

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    #principal data
    principal_asset = fields.Char(string='Principal Asset')
    asset_category = fields.Selection([('0', 'Fixed Asset'), ('1', 'License'), ('2', 'Proyect'), ('3', 'Leasing')])
    asset_code = fields.Char(string='Asset Code')

    # asset data
    producer = fields.Char(string='Producer')
    employee_id = fields.Many2one('hr.employee', string='Responsable')
    identification_number = fields.Char(string='identification', related='employee_id.identification_id')
    ubication = fields.Char(string='Ubication')
    capitalization_date = fields.Date(string='Capitalization Date')

    depreciation_entries_count_niff = fields.Integer(compute='_entry_count_niff', string='# Posted Depreciation Entries')
    gross_increase_count_niff = fields.Integer(compute='_entry_count_niff', string='# Gross Increases', help="Number of assets made to increase the value of the asset")
    total_depreciation_entries_count_niff = fields.Integer(compute='_entry_count_niff', string='# Depreciation Entries', help="Number of depreciation entries (posted or not)")

    # Depreciation params
    method_niff = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive'), ('degressive_then_linear', 'Accelerated Degressive')], string='Method', readonly=True, states={'draft': [('readonly', False)], 'model': [('readonly', False)]}, default='linear',
        help="Choose the method to use to compute the amount of depreciation lines.\n"
            "  * Linear: Calculated on basis of: Gross Value / Number of Depreciations\n"
            "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor\n"
            "  * Accelerated Degressive: Like Degressive but with a minimum depreciation value equal to the linear value.")
    method_number_niff = fields.Integer(string='Number of Depreciations', readonly=True, states={'draft': [('readonly', False)], 'model': [('readonly', False)]}, default=5, help="The number of depreciations needed to depreciate your asset")
    method_period_niff = fields.Selection([('1', 'Months'), ('12', 'Years')], string='Number of Months in a Period', readonly=True, default='12', states={'draft': [('readonly', False)], 'model': [('readonly', False)]},
        help="The amount of time between two depreciations")
    method_progress_factor_niff = fields.Float(string='Degressive Factor', readonly=True, default=0.3, states={'draft': [('readonly', False)], 'model': [('readonly', False)]})
    prorata_niff = fields.Boolean(string='Prorata Temporis', readonly=True, states={'draft': [('readonly', False)], 'model': [('readonly', False)]},
        help='Indicates that the first depreciation entry for this asset have to be done from the asset date (purchase date) instead of the first January / Start date of fiscal year')
    prorata_date_niff = fields.Date(
        string='Prorata Date',
        readonly=True, states={'draft': [('readonly', False)]})
    account_asset_id_niff = fields.Many2one('account.account', string='Fixed Asset Account', compute='_compute_value_niff', help="Account used to record the purchase of the asset at its original price.", store=True, states={'model': [('readonly', False)]}, domain="[('company_id', '=', company_id)]")
    account_depreciation_id_niff = fields.Many2one('account.account', string='Depreciation Account', readonly=True, states={'model': [('readonly', False)]}, domain="[('internal_type', '=', 'other'), ('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used in the depreciation entries, to decrease the asset value.")
    account_depreciation_expense_id_niff = fields.Many2one('account.account', string='Expense Account', readonly=True, states={'model': [('readonly', False)]}, domain="[('internal_type', '=', 'other'), ('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used in the periodical entries, to record a part of the asset as expense.")

    # override readonly states
    account_asset_id = fields.Many2one(states={'model': [('readonly', False)]})
    account_depreciation_id = fields.Many2one(states={'model': [('readonly', False)]})
    account_depreciation_expense_id = fields.Many2one(states={'model': [('readonly', False)]})

    journal_id_niff = fields.Many2one('account.journal', string='Journal', readonly=True, states={'draft': [('readonly', False)], 'model': [('readonly', False)]}, domain="[('type', '=', 'general'), ('company_id', '=', company_id)]")

    # Values
    original_value_niff = fields.Monetary(string="Original Value", compute='_compute_value_niff', inverse='_set_value_niff', store=True, readonly=True, states={'draft': [('readonly', False)]})
    book_value_niff = fields.Monetary(string='Book Value', readonly=True, compute='_compute_book_value_niff', store=True, help="Sum of the depreciable value, the salvage value and the book value of all value increase items")
    value_residual_niff = fields.Monetary(string='Depreciable Value', digits=0, readonly="1")
    salvage_value_niff = fields.Monetary(string='Not Depreciable Value', digits=0, readonly=True, states={'draft': [('readonly', False)]},
                                    help="It is the amount you plan to have that you cannot depreciate.")
    gross_increase_value_niff = fields.Monetary(string="Gross Increase Value", compute="_compute_book_value_niff", compute_sudo=True)

    # Links with entries
    depreciation_move_ids_niff = fields.One2many('account.move', compute='_compute_depreciation_move_ids_childs', string='Depreciation Lines', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)], 'paused': [('readonly', False)]})
    depreciation_move_ids_fiscal = fields.One2many('account.move', compute='_compute_depreciation_move_ids_childs', string='Depreciation Lines', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)], 'paused': [('readonly', False)]})
    original_move_line_ids_niff = fields.One2many('account.move.line', 'asset_id', string='Journal Items', readonly=True, states={'draft': [('readonly', False)]}, copy=False)

    # Analytic
    account_analytic_id_niff = fields.Many2one('account.analytic.account', string='Analytic Account', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    analytic_tag_ids_niff = fields.Many2many('account.analytic.tag', 'account_analytic_tag_niff', string='Analytic Tag', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    # Dates
    first_depreciation_date_niff = fields.Date(
        string='First Depreciation Date',
        readonly=True, required=True, states={'draft': [('readonly', False)], 'model': [('required', False)]}, default=fields.Date.today(),
        help='Note that this date does not alter the computation of the first journal entry in case of prorata temporis assets. It simply changes its accounting date',
    )
    acquisition_date_niff = fields.Date(readonly=True, states={'draft': [('readonly', False)]}, store=True)
    disposal_date = fields.Date(readonly=True, states={'draft': [('readonly', False)]},)

    # model-related fields
    model_id = fields.Many2one('account.asset', string='Modelo NIFF', domain="[('company_id', '=', company_id)]")
    model_niff_id = fields.Many2one('account.asset', string='Modelo NIFF', domain="[('company_id', '=', company_id)]")
    user_type_id_niff = fields.Many2one('account.account.type', related="account_asset_id_niff.user_type_id", string="Type of the account")
    display_model_choice_niff = fields.Boolean(compute="_compute_value_niff", compute_sudo=True)
    display_account_asset_id_niff = fields.Boolean(compute="_compute_value_niff", compute_sudo=True)

    # Capital gain
    # parent_id_niff = fields.Many2one('account.asset', help="An asset has a parent when it is the result of gaining value")
    children_ids_niff = fields.One2many('account.asset', 'parent_id', help="The children are the gains in value of this asset")


    asset_parent_id = fields.Many2one('account.asset', string='Principal Asset', domain="[('id','!=',id),('asset_type', '=', 'purchase'), ('state', '!=', 'model'), ('parent_id', '=', False)]", readonly="True", states={'draft': [('readonly', False)]})
    product_id = fields.Many2one('product.template', string="Product")

    need_dismantlement = fields.Boolean(string='¿Aplica Desmantelamiento?')
    total_dismantlement = fields.Integer(compute='_compute_dismantlement')
    acumulated_dismantlement = fields.Float(string="Desmantelamiento Acumulado")
    dismantlement_db_account_id = fields.Many2one('account.account', string='Cuenta Provision DB', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    dismantlement_cr_account_id = fields.Many2one('account.account', string='Cuenta Provision CR', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    both_paused = fields.Boolean(default=False)
    niff_paused = fields.Boolean(default=False)
    fiscal_paused = fields.Boolean(default=False)
    can_value_niff = fields.Boolean(default=False, string='¿Aplica avaluo?')
    can_value = fields.Boolean(default=False, string='¿Aplica avaluo?')
    # has_changed es un campo para validar cuales activos se han cambiado y no se les ha realizado el recalculo de la tabla de amortizacion
    has_changed = fields.Boolean(default=False, string='¿ha cambiado?')
    # total_movements_niff = fields.Integer(compute='_compute_dismantlement', default=0)
    is_keep_or_inversion = fields.Boolean(string="¿mantenido para la venta o propiedad de inversion?", default=False)

    acumulated_valorization = fields.Float(string="Valorizacion Acumulada", compute='_compute_acumulated_values', inverse='_inverse_acumulated_valorization', store=True)
    acumulated_valorization_niff = fields.Float(string="Valorizacion Acumulada", compute='_compute_acumulated_values', inverse='_inverse_acumulated_valorization_niff',store=True)
    profit_account_id = fields.Many2one('account.account', string='Cuenta para ganancias', help="Account used to record earnings.", store=True, domain="[('company_id', '=', company_id)]")
    loss_account_id = fields.Many2one('account.account', string='Cuenta para perdidas', help="Account used to record losses.", store=True, domain="[('company_id', '=', company_id)]")
    profit_account_niff_id = fields.Many2one('account.account', string='Cuenta para ganancias', help="Account used to record earnings.", store=True, domain="[('company_id', '=', company_id)]")
    loss_account_niff_id = fields.Many2one('account.account', string='Cuenta para perdidas', help="Account used to record losses.", store=True, domain="[('company_id', '=', company_id)]")

    partner_id = fields.Many2one('res.partner', string='Tercero',
                            help="Partner used in the depreciation board.", 
                            domain="['|',('company_id','=',company_id),('company_id','=',False)]",
                            readonly=True, 
                            states={'draft': [('readonly', False)]}, store=True)

    #gain or loss accounts for disposition and sell

    sell_gain_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used to write the journal item in case of gain while selling an asset")
    sell_loss_account_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used to write the journal item in case of loss while selling an asset")

    sell_gain_account_niif_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used to write the journal item in case of gain while selling an asset")
    sell_loss_account_niff_id = fields.Many2one('account.account', domain="[('deprecated', '=', False), ('company_id', '=', company_id)]", help="Account used to write the journal item in case of loss while selling an asset")

    is_usa = fields.Boolean(compute='_compute_is_usa')

    tax_ids = fields.Many2many('account.tax', string='Taxes', domain="[('type_tax_use','=','sale'),'|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.depends('company_id')
    def _compute_is_usa(self):
        for record in self:
            if record.company_id.country_id.code in ('EU', 'US'):
                record.is_usa = True
            else:
                record.is_usa = False


    @api.depends('depreciation_move_ids')
    def _compute_acumulated_values(self):
        for asset in self:
            asset.acumulated_valorization_niff = (sum(asset.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'valorizacion_niff' and move.state == 'posted').mapped('amount_total'))
                                                - sum(asset.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'desvalorizacion_niff' and move.state == 'posted').mapped('amount_total')))
            asset.acumulated_valorization = (sum(asset.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'valorizacion_fiscal' and move.state == 'posted').mapped('amount_total'))
                                                - sum(asset.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'desvalorizacion_fiscal' and move.state == 'posted').mapped('amount_total')))
            #asset.acumulated_dismantlement = sum(asset.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'dismantlement' and move.state == 'posted').mapped('amount_total'))

    @api.depends('depreciation_move_ids','account_asset_id_niff')
    def _compute_dismantlement(self):
        for asset in self:
            # count, total = 0, 0
            count = 0
            for depreciation in asset.depreciation_move_ids:
                if depreciation.asset_clasification == 'dismantlement':
                    count += 1
            # movements = self.env['account.asset.movements'].search([('asset_id','=',self.id)])
            # total = len(movements)
            asset.total_dismantlement = count
            # asset.total_movements_niff = total

    def _inverse_acumulated_valorization(self):
        for record in self:
            print(record.acumulated_valorization)

    def _inverse_acumulated_valorization_niff(self):
        for record in self:
            print(record.acumulated_valorization_niff)

    @api.depends('depreciation_move_ids')
    def _compute_depreciation_move_ids_childs(self):
        for asset in self:
            asset.depreciation_move_ids_niff = asset.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'NIFF' or move.asset_clasification == 'NIFF_sale' 
                                                or move.asset_clasification == 'NIFF_disp' or move.asset_clasification == 'valorizacion_niff' or move.asset_clasification == 'desvalorizacion_niff' or move.asset_clasification == 'NIFF_move')
            asset.depreciation_move_ids_fiscal = asset.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'FISCAL' or move.asset_clasification == 'FISCAL_move' 
                                                or move.asset_clasification == 'valorizacion_fiscal' or move.asset_clasification == 'desvalorizacion_fiscal' or move.asset_clasification == 'FISCAL_sale' or move.asset_clasification == 'FISCAL_disp')

    @api.depends('original_move_line_ids_niff', 'original_move_line_ids_niff.account_id', 'asset_type')
    def _compute_value_niff(self):
        for record in self:
            misc_journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('company_id', '=', record.company_id.id)], limit=1)
            if not record.original_move_line_ids:
                record.account_asset_id_niff = record.account_asset_id_niff or False
                record.original_value_niff = record.original_value_niff or False
                record.display_model_choice_niff = record.state == 'draft' and self.env['account.asset'].search([('state', '=', 'model'), ('asset_type', '=', record.asset_type)])
                record.display_account_asset_id_niff = True
                continue
            if any(line.move_id.state == 'draft' for line in record.original_move_line_ids):
                raise UserError(_("All the lines should be posted"))
            if any(account != record.original_move_line_ids[0].account_id for account in record.original_move_line_ids.mapped('account_id')):
                raise UserError(_("All the lines should be from the same account"))
            record.account_asset_id_niff = record.original_move_line_ids[0].account_id
            record.display_model_choice_niff = record.state == 'draft' and len(self.env['account.asset'].search([('state', '=', 'model'), ('account_asset_id_niff.user_type_id', '=', record.user_type_id_niff.id)]))
            record.display_account_asset_id_niff = False
            if not record.journal_id_niff:
                record.journal_id_niff = misc_journal_id
            total_credit = sum(line.credit for line in record.original_move_line_ids)
            total_debit = sum(line.debit for line in record.original_move_line_ids)
            total_taxes = 0
            for line in record.original_move_line_ids:
                for tax in line.tax_ids:
                    if tax.is_asset:
                        total_taxes += (tax.amount/100)*line.price_subtotal
            # if record.company_id.country_id.code in ('EU', 'US'):
            if record.is_usa:
                record.original_value_niff = 0
            else:
                record.original_value_niff = total_credit + total_debit + total_taxes 
                if (total_credit and total_debit) or record.original_value_niff == 0:
                    raise UserError(_("You cannot create an asset from lines containing credit and debit on the account or with a null amount"))

    @api.depends('original_move_line_ids', 'original_move_line_ids.account_id', 'asset_type')
    def _compute_value(self):
        super(AccountAsset, self)._compute_value()
        for record in self:
            total_taxes = 0
            total_invoice = 0
            total_taxes = 0
            if record.asset_type == 'purchase':
                for line in record.original_move_line_ids:
                        for tax in line.tax_ids:
                            if tax.is_asset:
                                total_taxes += (tax.amount/100)*line.price_subtotal
                record.original_value = record.original_value + total_taxes
                record.value_residual = record.original_value - record.salvage_value
            elif record.asset_type == 'sale':
                if record.original_move_line_ids:
                    for line in record.original_move_line_ids:
                        total_invoice += line.price_subtotal
                    record.original_value = total_invoice
                
                #record.value_residual = record.original_value - record.salvage_value

    def _set_value_niff(self):
        for record in self:
            record.acquisition_date_niff = record.acquisition_date if record.acquisition_date else fields.Date.today() 
            record.first_depreciation_date_niff = record._get_first_depreciation_date_niff()
            record.value_residual_niff = record.original_value_niff - record.salvage_value_niff
            # record.name = record.name or (record.original_move_line_ids_niff and record.original_move_line_ids_niff[0].name or '')
            if not record.asset_type and 'asset_type' in self.env.context:
                record.asset_type = self.env.context['asset_type']
            if not record.asset_type and record.original_move_line_ids_niff:
                account = record.original_move_line_ids_niff.account_id
                record.asset_type = account.asset_type
            # record._onchange_depreciation_account_niff()

    def _set_value(self):
        for record in self:
            record.acquisition_date = min(record.original_move_line_ids.mapped('date') + [record.prorata_date or record.first_depreciation_date or fields.Date.today()] + [record.acquisition_date or fields.Date.today()])
            record.first_depreciation_date = record._get_first_depreciation_date()
            record.value_residual = record.original_value - record.salvage_value
            record.name = record.name or (record.original_move_line_ids and record.original_move_line_ids[0].name or '')
            if not record.asset_type and 'asset_type' in self.env.context:
                record.asset_type = self.env.context['asset_type']
            if not record.asset_type and record.original_move_line_ids:
                account = record.original_move_line_ids.account_id
                record.asset_type = account.asset_type

    @api.onchange('asset_parent_id')
    def onchange_asset_parent_id(self):
        if self.state == 'draft': 
            self.model_id = self.asset_parent_id.model_id
            self._onchange_model_id()
            self.model_niff_id = self.asset_parent_id.model_niff_id
            self._onchange_model_niff_id()
    

    @api.depends('value_residual_niff', 'salvage_value_niff', 'children_ids_niff.book_value_niff')
    def _compute_book_value_niff(self):
        for record in self:
            record.book_value_niff = record.value_residual_niff + record.salvage_value_niff + sum(record.children_ids_niff.mapped('book_value_niff')) + record.acumulated_valorization_niff
            record.gross_increase_value_niff = sum(record.children_ids_niff.mapped('original_value_niff'))

    # @api.depends('value_residual', 'salvage_value', 'children_ids.book_value')
    # def _compute_book_value(self):
    #     for record in self:
    #         record.book_value = record.value_residual + record.salvage_value + sum(record.children_ids.mapped('book_value'))
    #         record.gross_increase_value = sum(record.children_ids.mapped('original_value'))

    @api.onchange('salvage_value_niff')
    def _onchange_salvage_value_niff(self):
        # When we are configuring the asset we dont want the book value to change
        # when we change the salvage value because of _compute_book_value
        # we need to reduce value_residual to do that
        self.value_residual_niff = self.original_value_niff - self.salvage_value_niff

    @api.onchange('original_value_niff')
    def _onchange_value_niff(self):
        self._set_value_niff()

    @api.onchange('original_value')
    def _onchange_value(self):
        for record in self:
            if record.original_value != 0.0:
                record.original_value_niff = record.original_value if (record.original_value_niff == 0.0 and not record.is_usa) else record.original_value_niff  
        #super(AccountAsset, self)._onchange_value()
        

    @api.onchange('method_period')
    def _onchange_method_period_niff(self):
        self.first_depreciation_date_niff = self._get_first_depreciation_date_niff()

    @api.onchange('prorata_niff')
    def _onchange_prorata_niff(self):
        if self.prorata_niff:
            self.prorata_date_niff = fields.Date.today()

    @api.onchange('depreciation_move_ids')
    def _onchange_depreciation_move_ids_niff(self):
        seq = 0
        asset_remaining_value = self.value_residual_niff
        cumulated_depreciation = 0
        for m in self.depreciation_move_ids_niff.sorted(lambda x: x.date):
            seq += 1
            if not m.reversal_move_id:
                asset_remaining_value -= m.amount_total
                cumulated_depreciation += m.amount_total
            if not m.asset_manually_modified:
                continue
            m.asset_manually_modified = False
            m.asset_remaining_value = asset_remaining_value
            m.asset_depreciated_value = cumulated_depreciation
            for older_move in self.depreciation_move_ids.sorted(lambda x: x.date)[seq:]:
                if not older_move.reversal_move_id:
                    asset_remaining_value -= older_move.amount_total
                    cumulated_depreciation += older_move.amount_total
                older_move.asset_remaining_value = asset_remaining_value
                older_move.asset_depreciated_value = cumulated_depreciation

    @api.onchange("acquisition_date")
    def _onchange_acquisition_date(self):
        self.acquisition_date_niff = self.acquisition_date
        self.first_depreciation_date_niff = self._get_first_depreciation_date_niff()
        self.first_depreciation_date = self._get_first_depreciation_date()

    @api.onchange('model_id')
    def _onchange_model_id(self):
        cuenta_analitica = self.account_analytic_id
        super(AccountAsset, self)._onchange_model_id()
        self.account_analytic_id = cuenta_analitica.id
        self.account_asset_id = self.model_id.account_asset_id
        if self.state == 'draft':
            self.model_niff_id = self.model_id
            self._onchange_model_niff_id()
        if self.model_id.can_value:
            self.can_value = True
            self.profit_account_id = self.model_id.profit_account_id
            self.loss_account_id = self.model_id.loss_account_id
        else: 
            self.can_value = False
        #cuentas de gastos
        self.sell_gain_account_id = self.model_id.sell_gain_account_id
        self.sell_loss_account_id = self.model_id.sell_loss_account_id

        if self.asset_type == 'sale':
            self.tax_ids = self.model_id.tax_ids
        
        


    @api.onchange('model_niff_id')
    def _onchange_model_niff_id(self):
        model = self.model_niff_id
        if  model:
            self.method_niff = model.method_niff
            self.method_number_niff = model.method_number_niff
            self.method_period_niff = model.method_period_niff
            self.method_progress_factor_niff = model.method_progress_factor_niff
            self.prorata_niff = model.prorata_niff
            self.prorata_date_niff = fields.Date.today()
            # self.account_analytic_id = model.account_analytic_id
            self.analytic_tag_ids_niff = [(6, 0, model.analytic_tag_ids_niff.ids)]
            self.account_depreciation_id_niff = model.account_depreciation_id_niff
            self.account_asset_id_niff = model.account_asset_id_niff
            self.account_depreciation_expense_id_niff = model.account_depreciation_expense_id_niff
            self.journal_id_niff = model.journal_id_niff
            if model.need_dismantlement:
                self.need_dismantlement = True
                self.dismantlement_db_account_id = model.dismantlement_db_account_id
                self.dismantlement_cr_account_id = model.dismantlement_cr_account_id
            else: 
                self.need_dismantlement = False
            if model.can_value_niff:
                self.can_value_niff = True
                self.profit_account_niff_id = model.profit_account_niff_id
                self.loss_account_niff_id = model.loss_account_niff_id
            else: 
                self.can_value_niff = False
            self.is_keep_or_inversion = model.is_keep_or_inversion
            #cuentas de gastos
            self.sell_gain_account_niif_id = model.sell_gain_account_niif_id
            self.sell_loss_account_niff_id = model.sell_loss_account_niff_id
        
            
                

    @api.onchange('asset_type')
    def _onchange_type_niff(self):
        if self.state != 'model':
            if self.asset_type == 'sale':
                self.prorata_niff = True
                self.method_period_niff = '1'
            else:
                self.method_period_niff = '12'

    def _get_first_depreciation_date(self, vals={}):
        if not self.first_depreciation_date:
            pre_depreciation_date = fields.Date.to_date(vals.get('acquisition_date') or vals.get('date') or min(self.original_move_line_ids.mapped('date'), default=self.acquisition_date or fields.Date.today()))
            depreciation_date = pre_depreciation_date + relativedelta(day=31)
            # ... or fiscalyear depending the number of period
            if '12' in (self.method_period, vals.get('method_period')):
                depreciation_date = depreciation_date + relativedelta(month=int(self.company_id.fiscalyear_last_month))
                depreciation_date = depreciation_date + relativedelta(day=self.company_id.fiscalyear_last_day)
                if depreciation_date < pre_depreciation_date:
                    depreciation_date = depreciation_date + relativedelta(years=1)
        else:
            depreciation_date = self.first_depreciation_date
            depreciation_date = depreciation_date + relativedelta(day=31)
        return depreciation_date

    # @api.depends('acquisition_date_niff')
    def _get_first_depreciation_date_niff(self, vals={}):
        if vals.get('acquisition_date_niff'):
           date = vals.get('acquisition_date_niff') 
        else:
            date = self.acquisition_date_niff or fields.Date.today()
        month_days = calendar.monthrange(date.year, date.month)[1]
        date = date.replace(day=month_days)
        return date

    def unlink(self):
        for asset in self:
            if asset.state in ['open', 'paused', 'close']:
                raise UserError(_('You cannot delete a document that is in %s state.') % asset.state)
            for line in asset.original_move_line_ids:
                body = _('A document linked to %s has been deleted: ') % (line.name or _('this move'))
                body += '<a href=# data-oe-model=account.asset data-oe-id=%d>%s</a>' % (asset.id, asset.name)
                line.move_id.message_post(body=body)
        return super(AccountAsset, self).unlink()

    def _compute_board_amount_niff(self, computation_sequence, residual_amount, total_amount_to_depr, max_depreciation_nb, starting_sequence, depreciation_date):
        amount = 0
        if computation_sequence == max_depreciation_nb:
            # last depreciation always takes the asset residual amount
            amount = residual_amount
        else:
            if self.method_niff in ('degressive', 'degressive_then_linear'):
                amount = residual_amount * self.method_progress_factor_niff
            if self.method_niff in ('linear', 'degressive_then_linear'):
                nb_depreciation = max_depreciation_nb - starting_sequence
                if self.prorata_niff:
                    nb_depreciation -= 1
                linear_amount = min(total_amount_to_depr / nb_depreciation, residual_amount)
                if self.method_niff == 'degressive_then_linear':
                    amount = max(linear_amount, amount)
                else:
                    amount = linear_amount
        return amount

    def compute_depreciation_board_masive(self):
        number_niff = self.method_number_niff
        number_fiscal = self.method_number
        date_niff = self.first_depreciation_date_niff
        date_fiscal = self.first_depreciation_date
        depreciated_niff = len(self.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'NIFF' and move.state == 'posted')) or 0
        depreciated = len(self.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'FISCAL' and move.state == 'posted')) or 0
        date_for_niff = min(self.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'NIFF' and move.state == 'draft').mapped('date')) if self.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'NIFF' and move.state == 'draft') else fields.Date.today()
        date_for_fiscal = min(self.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'FISCAL' and move.state == 'draft').mapped('date')) if self.depreciation_move_ids.filtered(lambda move: move.asset_clasification == 'FISCAL' and move.state == 'draft') else fields.Date.today()
        self.method_number_niff -= depreciated_niff
        self.method_number -= depreciated
        self.first_depreciation_date_niff = date_for_niff or date_niff
        self.first_depreciation_date = date_for_fiscal or date_fiscal
        self.compute_depreciation_board()
        self.method_number_niff = number_niff
        self.method_number = number_fiscal
        self.first_depreciation_date_niff =  date_niff
        self.first_depreciation_date =  date_fiscal

    def _recompute_board_whit_taxes(self, newlines):
        total_taxes = {}
        taxes_names = self.tax_ids.mapped('name')

        for name in taxes_names:
            total_taxes.update({name:0}) if name not in total_taxes.keys() else False
            
        final_lines = []
        if self.original_move_line_ids:
            partner = self.original_move_line_ids[0].move_id.partner_id
            for move_line in self.original_move_line_ids:
                product_account = move_line.product_id.property_account_income_id or move_line.product_id.categ_id.property_account_income_categ_id
                final_lines.append([move_line.product_id, move_line.price_subtotal, move_line.tax_ids, product_account, 
                                    move_line.analytic_account_id or self.account_analytic_id or False, move_line.price_subtotal, move_line.partner_id])
        else:
            partner = self.partner_id
            final_lines.append([self, self.original_value, False, self.account_depreciation_id, 
                                    self.account_analytic_id or False, self.original_value, self.partner_id])

        for line in newlines:
            line['partner_id'] = partner.id
            del(line['line_ids'])

        newlines = self.env['account.move']._prepare_move_for_asset_depreciation_with_taxes(newlines, final_lines, self)
        return newlines
        

    def compute_depreciation_board(self):
        self.ensure_one()
        amount_change_ids = self.depreciation_move_ids.filtered(lambda x: x.asset_value_change and not x.reversal_move_id and x.asset_clasification == 'FISCAL').sorted(key=lambda l: l.date)
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id and x.asset_clasification == 'FISCAL').sorted(key=lambda l: l.date)
        already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids])
        depreciation_number = self.method_number
        if self.prorata:
            depreciation_number += 1
        starting_sequence = 0
        amount_to_depreciate = self.value_residual + sum([m.amount_total for m in amount_change_ids])
        depreciation_date = self.first_depreciation_date
        # if we already have some previous validated entries, starting date is last entry + method period
        if posted_depreciation_move_ids and posted_depreciation_move_ids[-1].date:
            last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].date)
            if last_depreciation_date > depreciation_date:  # in case we unpause the asset
                depreciation_date = last_depreciation_date + relativedelta(months=+int(self.method_period))
        commands = [(2, line_id.id, False) for line_id in self.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'FISCAL')]
        newlines = self._recompute_board(depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids)
        if self.asset_type == 'sale':
            newlines = self._recompute_board_whit_taxes(newlines)
        newline_vals_list = []
        for newline_vals in newlines:
            # no need of amount field, as it is computed and we don't want to trigger its inverse function
            del(newline_vals['amount_total'])
            newline_vals['asset_clasification'] = "FISCAL"
            newline_vals_list.append(newline_vals)
        new_moves = self.env['account.move'].create(newline_vals_list)
        if self.asset_type == 'sale':
            for move in new_moves:
                copy = move.copy_data()
                move_copy = self.env['account.move'].new(copy[0])
                line_ids = move_copy.line_ids.filtered(lambda line: line.credit != 0)
                for line in line_ids:
                    line.recompute_tax_line = True
                move_copy._onchange_recompute_dynamic_lines()
                move.write(move_copy._convert_to_write(move_copy._cache))
                # move = self.env['account.move'].create(move._convert_to_write(move._cache))
        for move in new_moves:
            commands.append((4, move.id))
        self.write({'depreciation_move_ids': commands})
        if self.asset_type == 'purchase':
            self.compute_depreciation_board_niff()

    def compute_depreciation_board_niff(self):
        self.ensure_one()
        amount_change_ids = self.depreciation_move_ids.filtered(lambda x: x.asset_value_change and not x.reversal_move_id and x.asset_clasification == 'NIFF').sorted(key=lambda l: l.date)
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id and x.asset_clasification == 'NIFF').sorted(key=lambda l: l.date)
        already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids])
        depreciation_number = self.method_number_niff
        if self.prorata_niff:
            depreciation_number += 1
        starting_sequence = 0
        amount_to_depreciate = self.value_residual_niff + sum([m.amount_total for m in amount_change_ids])
        depreciation_date = self.first_depreciation_date_niff
        # if we already have some previous validated entries, starting date is last entry + method period
        if posted_depreciation_move_ids and posted_depreciation_move_ids[-1].date:
            last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].date)
            if last_depreciation_date > depreciation_date:  # in case we unpause the asset
                depreciation_date = last_depreciation_date + relativedelta(months=+int(self.method_period_niff))
        # commands = [(2, line_id.id, False) for line_id in self.depreciation_move_ids_niff.filtered(lambda x: x.state == 'draft')]
        commands = [(2, line_id.id, False) for line_id in self.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'NIFF')]
        newlines = self._recompute_board_niff(depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids)
        newline_vals_list = []
        for newline_vals in newlines:
            # no need of amount field, as it is computed and we don't want to trigger its inverse function
            del(newline_vals['amount_total'])
            newline_vals['asset_clasification'] = "NIFF"
            newline_vals_list.append(newline_vals)
        new_moves = self.env['account.move'].create(newline_vals_list)
        for move in new_moves:
            commands.append((4, move.id))
        # has_changed es un campo para validar cuales activos se han cambiado y no se les ha realizado el recalculo de la tabla de amortizacion
        if not self.has_changed:
                self.has_changed = False
        return self.write({'depreciation_move_ids': commands})

    def _recompute_board_niff(self, depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids):
        self.ensure_one()
        residual_amount = amount_to_depreciate
        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        move_vals = []
        prorata = self.prorata_niff and not self.env.context.get("ignore_prorata")
        if amount_to_depreciate != 0.0:
            for asset_sequence in range(starting_sequence + 1, depreciation_number + 1):
                while amount_change_ids and amount_change_ids[0].date <= depreciation_date:
                    if not amount_change_ids[0].reversal_move_id:
                        residual_amount -= amount_change_ids[0].amount_total
                        amount_to_depreciate -= amount_change_ids[0].amount_total
                        already_depreciated_amount += amount_change_ids[0].amount_total
                    amount_change_ids[0].write({
                        'asset_remaining_value': float_round(residual_amount, precision_rounding=self.currency_id.rounding),
                        'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                    })
                    amount_change_ids -= amount_change_ids[0]
                amount = self._compute_board_amount_niff(asset_sequence, residual_amount, amount_to_depreciate, depreciation_number, starting_sequence, depreciation_date)
                prorata_factor = 1
                move_ref = self.name + ' (%s/%s)' % (prorata and asset_sequence - 1 or asset_sequence, self.method_number_niff)
                if prorata and asset_sequence == 1:
                    move_ref = self.name + ' ' + _('(prorata entry)')
                    first_date = self.prorata_date_niff
                    if int(self.method_period_niff) % 12 != 0:
                        month_days = calendar.monthrange(first_date.year, first_date.month)[1]
                        days = month_days - first_date.day + 1
                        prorata_factor = days / month_days
                    else:
                        total_days = (depreciation_date.year % 4) and 365 or 366
                        days = (self.company_id.compute_fiscalyear_dates(first_date)['date_to'] - first_date).days + 1
                        prorata_factor = days / total_days
                amount = self.currency_id.round(amount * prorata_factor)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount

                move_vals.append(self.env['account.move']._prepare_move_for_asset_depreciation_niff({
                    'amount': amount,
                    'asset_id': self,
                    'move_ref': move_ref,
                    'date': depreciation_date,
                    'asset_remaining_value': float_round(residual_amount, precision_rounding=self.currency_id.rounding),
                    'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                }))

                depreciation_date = depreciation_date + relativedelta(months=+int(self.method_period_niff))
                # datetime doesn't take into account that the number of days is not the same for each month
                if (not self.prorata_niff or self.env.context.get("ignore_prorata")) and int(self.method_period_niff) % 12 != 0:
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=max_day_in_month)
        return move_vals



    def action_save_model(self):
        form_ref = {
            'purchase': 'account_asset.view_account_asset_form',
            'sale': 'account_asset.view_account_asset_revenue_form',
            'expense': 'account_asset.view_account_asset_expense_form',
        }.get(self.asset_type)

        return {
            'name': _('Save model'),
            'views': [[self.env.ref(form_ref).id, "form"]],
            'res_model': 'account.asset',
            'type': 'ir.actions.act_window',
            'context': {
                'default_state': 'model',
                'default_account_asset_id': self.account_asset_id.id,
                'default_account_depreciation_id': self.account_depreciation_id.id,
                'default_account_depreciation_expense_id': self.account_depreciation_expense_id.id,
                'default_journal_id': self.journal_id.id,
                'default_method': self.method,
                'default_method_number': self.method_number,
                'default_method_period': self.method_period,
                'default_method_progress_factor': self.method_progress_factor,
                'default_prorata': self.prorata,
                'default_prorata_date': self.prorata_date,
                'default_analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                'original_asset': self.id,

                'default_account_asset_id_niff': self.account_asset_id_niff.id,
                'default_account_depreciation_id_niff': self.account_depreciation_id_niff.id,
                'default_account_depreciation_expense_id_niff': self.account_depreciation_expense_id_niff.id,
                'default_journal_id_niff': self.journal_id_niff.id,
                'default_method_niff': self.method_niff,
                'default_method_number_niff': self.method_number_niff,
                'default_method_period_niff': self.method_period_niff,
                'default_method_progress_factor_niff': self.method_progress_factor_niff,
                'default_prorata_niff': self.prorata_niff,
                'default_prorata_date_niff': self.prorata_date_niff,
                'default_analytic_tag_ids_niff': [(6, 0, self.analytic_tag_ids_niff.ids)],
            }
        }

    def open_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.depreciation_move_ids.ids)],
            'context': dict(self._context, create=False),
        }


    def open_increase(self):
        return {
            'name': _('Gross Increase'),
            'view_mode': 'tree,form',
            'res_model': 'account.asset',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.children_ids.ids)],
            'views': self.env['account.asset']._get_views(self.asset_type),
        }
    
    def open_dismantlements(self):
        return {
            'name': _('Dismantlements Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.depreciation_move_ids.ids),('asset_clasification','=','dismantlement')],
            'context': dict(self._context, create=False)
        }

    # def open_movements(self):
    #     return {
    #         'name': _('Movements Entries'),
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.asset.movements',
    #         'views': [(self.env.ref('account_asset_extended.account_asset_movements_tree').id, 'tree'), (False, 'form')],
    #         'type': 'ir.actions.act_window',
    #         'domain': [('asset_id', '=', self.id)],
    #         'context': dict(self._context, create=False)
    #     }


    def validate(self):
        super(AccountAsset, self).validate()
        fields = [
            'method_niff',
            'method_number_niff',
            'method_period_niff',
            'method_progress_factor_niff',
            'salvage_value_niff',
            'original_move_line_ids_niff',
        ]
        ref_tracked_fields = self.env['account.asset'].fields_get(fields)
        self.write({'state': 'open'})
        for asset in self:
            tracked_fields = ref_tracked_fields.copy()
            if asset.method_niff == 'linear':
                del(tracked_fields['method_progress_factor_niff'])
            dummy, tracking_value_ids = asset._message_track(tracked_fields, dict.fromkeys(fields))
            asset_name = {
                'purchase': (_('Asset created'), _('An asset has been created for this move:')),
                'sale': (_('Deferred revenue created'), _('A deferred revenue has been created for this move:')),
                'expense': (_('Deferred expense created'), _('A deferred expense has been created for this move:')),
            }[asset.asset_type]
            msg = asset_name[1] + ' <a href=# data-oe-model=account.asset data-oe-id=%d>%s</a>' % (asset.id, asset.name)
            asset.message_post(body=asset_name[0], tracking_value_ids=tracking_value_ids)
            for move_id in asset.original_move_line_ids_niff.mapped('move_id'):
                move_id.message_post(body=msg)
            if not asset.depreciation_move_ids_niff:
                asset.compute_depreciation_board()
            asset._check_depreciations_niff()
            asset.depreciation_move_ids_niff.write({'auto_post': True})


    def _get_disposal_moves(self, invoice_line_ids, disposal_date, gain_account, loss_account):
        def get_line(asset, amount, account):
            # account_analytic_id = asset.account_analytic_id
            return (0, 0, {
                'name': asset.name,
                'account_id': account.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * asset.value_residual or 0.0,
            })

        move_ids = []
        assert len(self) == len(invoice_line_ids)
        for asset, invoice_line_id in zip(self, invoice_line_ids):
            dates = asset.depreciation_move_ids.filtered(lambda x: not x.reversal_move_id and x.state == 'posted' and x.asset_clasification == 'FISCAL').mapped('date')
            if dates:
                if disposal_date < max(dates or [fields.Date.today()]):
                    if invoice_line_id:
                        raise UserError('There are depreciation posted after the invoice date (%s).\nPlease revert them or change the date of the invoice.' % disposal_date)
                    else:
                        raise UserError('There are depreciation posted in the future, please revert them.')
            account_analytic_id = asset.account_analytic_id
            analytic_tag_ids = asset.analytic_tag_ids
            company_currency = asset.company_id.currency_id
            current_currency = asset.currency_id
            prec = company_currency.decimal_places
            unposted_depreciation_move_ids = asset.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'FISCAL')
            # if unposted_depreciation_move_ids:
            old_values = {
                'method_number': asset.method_number,
            }

            # Remove all unposted depr. lines
            commands = [(2, line_id.id, False) for line_id in unposted_depreciation_move_ids]

            # Create a new depr. line with the residual amount and post it
            asset_sequence = len(asset.depreciation_move_ids.filtered(lambda x: x.asset_clasification == 'FISCAL')) - (len(unposted_depreciation_move_ids) or 0) + 1

            childs_total = 0
            childs_total_depreciated = 0
            childs_ids = self.env['account.asset'].search([('asset_parent_id','=',self.id),('state','not in',('model','draft'))])
            if childs_ids:
                for child in childs_ids:
                    child_initial_amount = child.original_value                    
                    childs_total += child_initial_amount
                    child_depreciated_amount = copysign(sum(child.depreciation_move_ids.filtered(lambda r: r.state == 'posted' and r.asset_clasification == 'FISCAL').mapped('amount_total')), -child_initial_amount)
                    childs_total_depreciated += child_depreciated_amount
            initial_amount = asset.original_value
            initial_account = asset.original_move_line_ids.account_id if len(asset.original_move_line_ids.account_id) == 1 else asset.account_asset_id
            depreciated_amount = copysign(sum(asset.depreciation_move_ids.filtered(lambda r: r.state == 'posted' and r.asset_clasification == 'FISCAL').mapped('amount_total')), -initial_amount)
            depreciation_account = asset.account_depreciation_id
            invoice_amount = copysign(invoice_line_id.price_subtotal, -initial_amount)
            invoice_account = invoice_line_id.account_id
            difference = -initial_amount - depreciated_amount - invoice_amount - childs_total - childs_total_depreciated
            # difference_account = asset.company_id.gain_account_id if difference > 0 else asset.company_id.loss_account_id
            difference_account = gain_account if difference > 0 else loss_account
            line_datas = [(asset, initial_amount, initial_account), (asset, depreciated_amount, depreciation_account), (asset, invoice_amount, invoice_account), (asset, difference, difference_account)]
            if not invoice_line_id:
                del line_datas[2]
            
            if childs_ids:
                for child in childs_ids:
                    child_initial_amount = child.original_value
                    child_depreciated_amount = copysign(sum(child.depreciation_move_ids.filtered(lambda r: r.state == 'posted' and r.asset_clasification == 'FISCAL').mapped('amount_total')), -child_initial_amount)
                    child_initial_account = child.account_asset_id
                    child_depreciation_account = child.account_depreciation_id
                    if not child_initial_account or not child_depreciation_account:
                        raise UserError(_('The asset %s don\'t have asset account or depreciation account')%(child.name))
                    line_datas.append((child, child_initial_amount, child_initial_account))
                    line_datas.append((child, child_depreciated_amount, child_depreciation_account))
                    del_commands = [(2, line_id.id, False) for line_id in child.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'FISCAL')]
                    child.write({'state' : 'close', 'depreciation_move_ids': del_commands})
                    
            vals = {
                'amount_total': current_currency._convert(asset.value_residual, company_currency, asset.company_id, disposal_date),
                'asset_id': asset.id,
                'ref': asset.name + ': ' + (_('Disposal') if not invoice_line_id else _('Sale')) + ' asset value',
                'asset_remaining_value': 0,
                'asset_depreciated_value': max(asset.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'FISCAL'), key=lambda x: x.date, default=self.env['account.move']).asset_depreciated_value,
                'date': disposal_date,
                'asset_clasification': 'FISCAL_disp' if not invoice_line_id else 'FISCAL_sale',
                'journal_id': asset.journal_id.id,
                'line_ids': [get_line(asset, amount, account) for asset, amount, account in line_datas if account],
            }
            commands.append((0, 0, vals))
            asset.write({'depreciation_move_ids': commands, 'method_number': asset_sequence})
            
            moves_valorization = asset.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'valorizacion_fiscal')
            childs_valorization = sum(childs_ids.mapped('acumulated_valorization'))
            
            if moves_valorization or childs_valorization != 0:
                line_datas = []
                total_valorization = 0
                if moves_valorization:
                    total_valorization = self.acumulated_valorization
                    line_datas = [(asset, total_valorization, self.profit_account_id), (asset, -total_valorization, self.loss_account_id)]
                if childs_valorization != 0:
                    for child in childs_ids:
                        total_valorization_child = child.acumulated_valorization
                        if not child.profit_account_id or not child.loss_account_id:
                            raise UserError(_('The asset %s don\'t have profit or loss account')%(child.name))
                        line_datas.append((child, total_valorization_child, child.profit_account_id))
                        line_datas.append((child, -total_valorization_child, child.loss_account_id))
                        total_valorization += total_valorization_child
                vals = {
                        'amount_total': abs(total_valorization),
                        'asset_id': self.id,
                        'ref': asset.name + ': ' + (_('Disposal') if not invoice_line_id else _('Sale')) + ' asset depreciation value',
                        'type': 'entry',
                        'asset_remaining_value': 0,
                        'asset_depreciated_value': 0,
                        'date': disposal_date,
                        'journal_id': self.journal_id_niff.id,
                        'asset_clasification': 'FISCAL_disp' if not invoice_line_id else 'FISCAL_sale',
                        'line_ids': [get_line(asset, amount, account) for asset, amount, account in line_datas if account],
                    }
                self.write({'depreciation_move_ids': [(0,0,vals)]})
            tracked_fields = self.env['account.asset'].fields_get(['method_number'])
            changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
            if changes:
                asset.message_post(body=_('Asset sold or disposed. Accounting entry awaiting for validation.'), tracking_value_ids=tracking_value_ids)
            move_ids += self.env['account.move'].search([('asset_id', '=', asset.id), ('state', '=', 'draft'), ('asset_clasification','in',('FISCAL_sale','FISCAL_disp'))]).ids

        return move_ids

    def _get_disposal_moves_niff(self, invoice_line_ids, disposal_date, gain_account_niif, loss_account_niif):
        def get_line(asset, amount, account):
            account_analytic_id = asset.account_analytic_id
            return (0, 0, {
                'name': asset.name,
                'account_id': account.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * asset.value_residual or 0.0,
            })

        move_ids = []
        assert len(self) == len(invoice_line_ids)
        for asset, invoice_line_id in zip(self, invoice_line_ids):

            if asset.original_value_niff == 0:
                continue

            dates = asset.depreciation_move_ids.filtered(lambda x: not x.reversal_move_id and x.state == 'posted' and x.asset_clasification == 'NIFF').mapped('date')
            if dates:
                if disposal_date < max(dates or [fields.Date.today()]):
                    if invoice_line_id:
                        raise UserError('There are depreciation posted after the invoice date (%s).\nPlease revert them or change the date of the invoice.' % disposal_date)
                    else:
                        raise UserError('There are depreciation posted in the future, please revert them.')
            account_analytic_id = asset.account_analytic_id
            analytic_tag_ids = asset.analytic_tag_ids
            company_currency = asset.company_id.currency_id
            current_currency = asset.currency_id
            prec = company_currency.decimal_places
            unposted_depreciation_move_ids = asset.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'NIFF')
            # if unposted_depreciation_move_ids:
                # old_values = {
                #     'method_number': asset.method_number,
                # }

                # Remove all unposted depr. lines
            commands = [(2, line_id.id, False) for line_id in unposted_depreciation_move_ids]

            # Create a new depr. line with the residual amount and post it
            asset_sequence = len(asset.depreciation_move_ids.filtered(lambda x: x.asset_clasification == 'NIFF')) - (len(unposted_depreciation_move_ids) or 0) + 1

            childs_total = 0
            childs_total_depreciated = 0
            childs_ids = self.env['account.asset'].search([('asset_parent_id','=',self.id),('state','not in',('model','draft'))])
            if childs_ids:
                for child in childs_ids:
                    child_initial_amount = child.original_value_niff                
                    childs_total += child_initial_amount
                    child_depreciated_amount = copysign(sum(child.depreciation_move_ids.filtered(lambda r: r.state == 'posted' and r.asset_clasification == 'NIFF').mapped('amount_total')), -child_initial_amount)
                    childs_total_depreciated += child_depreciated_amount
                    if self.is_keep_or_inversion:
                        childs_total += child.acumulated_valorization_niff

            initial_amount = asset.original_value
            initial_account = asset.account_asset_id_niff
            depreciated_amount = copysign(sum(asset.depreciation_move_ids.filtered(lambda r: r.state == 'posted' and r.asset_clasification == 'NIFF').mapped('amount_total')), -initial_amount)
            depreciation_account = asset.account_depreciation_id_niff
            invoice_amount = copysign(invoice_line_id.price_subtotal, -initial_amount)
            invoice_account = invoice_line_id.account_id
            difference = -initial_amount - depreciated_amount - invoice_amount - childs_total - childs_total_depreciated
            # difference_account = asset.company_id.gain_account_id if difference > 0 else asset.company_id.loss_account_id
            difference_account = gain_account_niif if difference > 0 else loss_account_niif
            if self.is_keep_or_inversion:
                line_datas = [(asset, initial_amount, initial_account), (asset, depreciated_amount, depreciation_account), (asset, invoice_amount, invoice_account), (asset, difference - self.acumulated_valorization_niff, difference_account),(asset, self.acumulated_valorization_niff ,initial_account)]
            else:
                line_datas = [(asset, initial_amount, initial_account), (asset, depreciated_amount, depreciation_account), (asset, invoice_amount, invoice_account), (asset, difference, difference_account)]
            if not invoice_line_id:
                del line_datas[2]

            if childs_ids:
                for child in childs_ids:
                    child_initial_amount = child.original_value_niff
                    child_depreciated_amount = copysign(sum(child.depreciation_move_ids.filtered(lambda r: r.state == 'posted' and r.asset_clasification == 'NIFF').mapped('amount_total')), -child_initial_amount)
                    child_initial_account = child.account_asset_id_niff
                    child_depreciation_account = child.account_depreciation_id_niff
                    if not child_initial_account or not child_depreciation_account:
                        raise UserError(_('The asset %s don\'t have asset account or depreciation account for niff contability')%(child.name))
                    line_datas.append((child, child_initial_amount, child_initial_account))
                    line_datas.append((child, child_depreciated_amount, child_depreciation_account))
                    if self.is_keep_or_inversion and child.acumulated_valorization_niff != 0:
                        line_datas.append((child, child.acumulated_valorization_niff ,initial_account))
                    del_commands = [(2, line_id.id, False) for line_id in child.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'NIFF')]
                    child.write({'state' : 'close', 'depreciation_move_ids': del_commands})

            vals = {
                'amount_total': current_currency._convert(asset.value_residual, company_currency, asset.company_id, disposal_date),
                'asset_id': asset.id,
                'ref': asset.name + ': ' + (_('Disposal') if not invoice_line_id else _('Sale')) + ' asset value',
                'asset_remaining_value': 0,
                'asset_depreciated_value': max(asset.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'NIFF'), key=lambda x: x.date, default=self.env['account.move']).asset_depreciated_value,
                'date': disposal_date,
                'asset_clasification': 'NIFF_disp' if not invoice_line_id else 'NIFF_sale',
                'journal_id': asset.journal_id_niff.id,
                'line_ids': [get_line(asset, amount, account) for asset, amount, account in line_datas if account],
            }
            commands.append((0, 0, vals))
            asset.write({'depreciation_move_ids': commands, 'method_number_niff': asset_sequence})

            moves_valorization = asset.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'valorizacion_niff')
            childs_valorization = sum(childs_ids.mapped('acumulated_valorization_niff'))

            if (moves_valorization or childs_valorization) and not self.is_keep_or_inversion:
                line_datas = []
                total_valorization = 0
                if moves_valorization:
                    total_valorization = self.acumulated_valorization_niff
                    valorization_account = self.profit_account_niff_id if total_valorization >=0 else self.loss_account_niff_id
                    line_datas = [(asset, total_valorization, self.account_asset_id), (asset, -total_valorization, valorization_account)]
                if childs_ids:
                    for child in childs_ids:
                        if child.acumulated_valorization_niff != 0:
                            child_total_valorization = child.acumulated_valorization_niff
                            childs_valorization_account = child.profit_account_niff_id if child_total_valorization > 0 else child.loss_account_niff_id
                            line_datas.append((child, total_valorization, child.account_asset_id))
                            line_datas.append((child, -total_valorization, childs_valorization_account))
                            total_valorization += child_total_valorization

                vals = {
                    'amount_total': abs(total_valorization),
                    'asset_id': self.id,
                    'ref': asset.name + ': ' + (_('Disposal') if not invoice_line_id else _('Sale')) + ' asset depreciation value',
                    'type': 'entry',
                    'asset_remaining_value': 0,
                    'asset_depreciated_value': 0,
                    'date': disposal_date,
                    'journal_id': self.journal_id_niff.id,
                    'asset_clasification': 'NIFF_disp' if not invoice_line_id else 'NIFF_sale',
                    'line_ids': [get_line(asset, amount, account) for asset, amount, account in line_datas if account],
                }
                self.write({'depreciation_move_ids': [(0,0,vals)]})

            if self.acumulated_dismantlement != 0:
                if not self.dismantlement_db_account_id or not self.dismantlement_cr_account_id:
                    raise UserError(_('Cuentas de desmantelamiento no configuradas'))
                line_datas = [(asset, self.acumulated_dismantlement, self.dismantlement_db_account_id),(asset, -self.acumulated_dismantlement, self.dismantlement_cr_account_id)]
                if childs_ids:
                    for child in childs_ids:
                        if child.acumulated_dismantlement != 0:
                            if not child.dismantlement_db_account_id or not child.dismantlement_cr_account_id:
                                raise UserError(_('Cuentas de desmantelamiento no configuradas para el activo %s')%(child.name))
                            line_datas.append((child, child.acumulated_dismantlement, child.dismantlement_db_account_id))
                            line_datas.append((child, -child.acumulated_dismantlement, child.dismantlement_cr_account_id))
                vals = {
                    'amount_total': abs(self.acumulated_dismantlement),
                    'asset_id': self.id,
                    'ref': asset.name + ': ' + (_('Disposal') if not invoice_line_id else _('Sale')) + ' asset dismantlement value',
                    'type': 'entry',
                    'asset_remaining_value': 0,
                    'asset_depreciated_value': 0,
                    'date': disposal_date,
                    'journal_id': self.journal_id_niff.id,
                    'asset_clasification': 'NIFF_disp' if not invoice_line_id else 'NIFF_sale',
                    'line_ids': [get_line(asset, amount, account) for asset, amount, account in line_datas if account],
                }
                self.write({'depreciation_move_ids': [(0,0,vals)]})
            # tracked_fields = self.env['account.asset'].fields_get(['method_number_niff'])
            # changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
            # if changes:
            #     asset.message_post(body=_('Asset sold or disposed. Accounting entry awaiting for validation.'), tracking_value_ids=tracking_value_ids)
            move_ids += self.env['account.move'].search([('asset_id', '=', asset.id), ('state', '=', 'draft'), ('asset_clasification','in',('NIFF_disp','NIFF_sale'))]).ids

        return move_ids

#cuidado y aca voy
    def set_to_close(self, invoice_line_id, date=None, gain_account=None, loss_account=None, gain_account_niif=None, loss_account_niif=None):
        self.ensure_one()
        disposal_date = date or fields.Date.today()
        if self.children_ids.filtered(lambda a: a.state in ('draft', 'open') or a.value_residual > 0):
            raise UserError(_("You cannot automate the journal entry for an asset that has a running gross increase. Please use 'Dispose' on the increase(s)."))
        full_asset = self + self.children_ids
        move_ids = full_asset._get_disposal_moves([invoice_line_id] * len(full_asset), disposal_date, gain_account, loss_account)
        move_ids_niff = full_asset._get_disposal_moves_niff([invoice_line_id] * len(full_asset), disposal_date, gain_account_niif, loss_account_niif)
        move_ids += move_ids_niff
        self.write({'state': 'close', 'disposal_date': disposal_date})
        # self.model_id = model_id
        # self.model_id_niff = model_id
        if move_ids:
            return self._return_disposal_view(move_ids)

    def set_to_running(self):
        if self.depreciation_move_ids_niff and not max(self.depreciation_move_ids_niff, key=lambda m: m.date).asset_remaining_value == 0:
            self.env['asset.modify'].create({'asset_id': self.id, 'name': _('Reset to running')}).modify()
        self.write({'state': 'open', 'disposal_date': False})


    def _insert_depreciation_line_niff(self, line_before, amount, label, depreciation_date):
        """ Inserts a new line in the depreciation board, shifting the sequence of
        all the following lines from one unit.
        :param line_before:     The depreciation line after which to insert the new line,
                                or none if the inserted line should take the first position.
        :param amount:          The depreciation amount of the new line.
        :param label:           The name to give to the new line.
        :param date:            The date to give to the new line.
        """
        self.ensure_one()
        moveObj = self.env['account.move']

        new_line = moveObj.create(moveObj._prepare_move_for_asset_depreciation({
            'amount': amount,
            'asset_id': self,
            'move_ref': self.name + ': ' + label,
            'date': depreciation_date,
            'asset_remaining_value': self.value_residual_niff - amount,
            'asset_depreciated_value': line_before and (line_before.asset_depreciated_value + amount) or amount,
        }))
        return new_line

    @api.depends('depreciation_move_ids.state', 'parent_id')
    def _entry_count_niff(self):
        for asset in self:
            res = self.env['account.move'].search_count([('asset_id', '=', asset.id), ('state', '=', 'posted'), ('reversal_move_id', '=', False)])
            asset.depreciation_entries_count_niff = res or 0
            asset.total_depreciation_entries_count_niff = len(asset.depreciation_move_ids_niff)
            asset.gross_increase_count_niff = len(asset.children_ids_niff)


######################
    def copy_data(self, default=None):
        if default is None:
            default = {}
        if self.state == 'model':
            default.update(state='model')
        default['name'] = self.name + _(' (copy)')
        default['account_asset_id'] = self.account_asset_id.id
        default['account_asset_id_niff'] = self.account_asset_id_niff.id
        default['acumulated_valorization_niff'] = 0
        default['acumulated_valorization'] = 0
        return super(AccountAsset, self).copy_data(default)

######################

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('asset_type') == 'purchase' and vals.get('state') != 'model' :
                asset_obj = self.env['account.asset'].search([('product_id','=',vals.get('product_id'))])
                if asset_obj:
                    raise UserError(_('An asset already exists with this product. (%s)')%(asset_obj[0].name))
            # original_move_line_ids_niff = 'original_move_line_ids_niff' in vals and self._check_original_move_line_ids_niff(vals['original_move_line_ids_niff'])
            if 'state' in vals and vals['state'] != 'draft' and not (set(vals) - set({'account_depreciation_id_niff', 'account_depreciation_expense_id_niff', 'journal_id_niff'})):
                raise UserError(_("Some required values are missing"))
            if 'first_depreciation_date_niff' not in vals:
                if 'acquisition_date_niff' in vals:
                    vals['first_depreciation_date_niff'] = self._get_first_depreciation_date_niff(vals)
                else:
                    vals['first_depreciation_date_niff'] = fields.Date.today()
            #     elif original_move_line_ids_niff and 'date' in original_move_line_ids_niff[0]:
            #         vals['first_depreciation_date_niff'] = self._get_first_depreciation_date_niff(original_move_line_ids_niff[0])
            #     else:
            #         vals['first_depreciation_date_niff'] = self._get_first_depreciation_date_niff()
            if self._context.get('import_file', False) and 'category_id' in vals:
                changed_vals = self.onchange_category_id_values(vals['category_id'])['value']
                # To avoid to overwrite vals explicitly set by the import
                [changed_vals.pop(key, None) for  key in vals.keys()]
                vals.update(changed_vals)
        new_recs = super(AccountAsset, self).create(vals_list)
        with self.env.norecompute():
            # new_recs = super(AccountAsset, self.with_context(mail_create_nolog=True)).create(vals_list)
            if self.env.context.get('original_asset'):
                # When original_asset is set, only one asset is created since its from the form view
                original_asset = self.env['account.asset'].browse(self.env.context.get('original_asset'))
                original_asset.model_id_niff = new_recs
        if not self._context.get('import_file', False):
            new_recs.filtered(lambda r: r.state != 'model')._set_value_niff()
        # super(AccountAsset, self).create(vals_list)
        return new_recs

    def write(self, vals):
        # super(AccountAsset, self).write(vals)
        # 'original_move_line_ids_niff' in vals and self._check_original_move_line_ids_niff(vals['original_move_line_ids_niff'])
        if vals.get('account_analytic_id'):
            account_analytic_id = self.env['account.analytic.account'].browse(vals.get('account_analytic_id'))
            if account_analytic_id != self.account_analytic_id:
                if not self.account_analytic_id:
                    body = _('El centro de costo ha cambiado a %s, modificacion hecha por %s') % (account_analytic_id.name, self.env.user.name)
                else:
                    body = _('El centro de costo ha cambiado de %s a %s, modificacion hecha por %s') % (self.account_analytic_id.name, account_analytic_id.name, self.env.user.name)
                self.message_post(body=body)
                moves = self.depreciation_move_ids.filtered(lambda x: x.state == 'draft')
                for move in moves:
                    lines = move.line_ids
                    for line in lines:
                        line.analytic_account_id = account_analytic_id
                if not self.has_changed:
                    self.has_changed = True

        if (vals.get('method_number') or vals.get('method_period')) and self.id:
            number = vals.get('method_number') or self.method_number
            period_number = vals.get('method_period') or self.method_period
            body = _('El periodo de la amortizacion ha sido modificado a %s %s por %s para la contabilidad FISCAL') % (period_number, number, self.env.user.name or 'el sistema')
            self.message_post(body=body)                                                                                        
            if not self.has_changed:
                self.has_changed = True

        if (vals.get('method_number_niff') or vals.get('method_period_niff')) and self.id:
            number = vals.get('method_number_niff') or self.method_number_niff
            period_number = vals.get('method_period_niff') or self.method_period_niff
            body = _('El periodo de la amortizacion ha sido modificado a %s %s por %s para la contabilidad NIFF') % (period_number, number, self.env.user.name or 'el sistema')
            self.message_post(body=body)                                                                                        
            if not self.has_changed:
                self.has_changed = True

        res = super(AccountAsset, self).write(vals)
        return res

    # @api.constrains('active', 'state')
    # def _check_active(self):
    #     for record in self:
    #         if not record.active and record.state != 'close':
    #             raise UserError(_('You cannot archive a record that is not closed'))

    @api.constrains('depreciation_move_ids_niff')
    def _check_depreciations_niff(self):
        for record in self:
            if record.state == 'open' and record.depreciation_move_ids_niff and not record.currency_id.is_zero(record.depreciation_move_ids_niff.filtered(lambda x: not x.reversal_move_id).sorted(lambda x: (x.date, x.id))[-1].asset_remaining_value):
                raise UserError(_("The remaining value on the last depreciation line must be 0"))

    def _check_original_move_line_ids_niff(self, original_move_line_ids_niff):
        original_move_line_ids_niff = self.resolve_2many_commands('original_move_line_ids_niff', original_move_line_ids_niff) or []
        if any(line.get('asset_id') for line in original_move_line_ids_niff):
            raise UserError(_("One of the selected Journal Items already has a depreciation associated"))
        return original_move_line_ids_niff

    def pause_diferent(self, pause_date, asset_pause_type):
        """ Sets an 'open' asset in 'paused' state, generating first a depreciation
        line corresponding to the ratio of time spent within the current depreciation
        period before putting the asset in pause. This line and all the previous
        unposted ones are then posted.
        """
        self.ensure_one()

        all_lines_before_pause = self.depreciation_move_ids.filtered(lambda x: x.date <= pause_date and x.asset_clasification == asset_pause_type)
        line_before_pause = all_lines_before_pause and max(all_lines_before_pause, key=lambda x: x.date)
        following_lines = self.depreciation_move_ids.filtered(lambda x: x.date > pause_date and x.asset_clasification == asset_pause_type)
        if following_lines:
            if any(line.state == 'posted' for line in following_lines):
                raise UserError(_("You cannot pause an asset with posted depreciation lines in the future."))

            if self.prorata:
                first_following = min(following_lines, key=lambda x: x.date)
                depreciation_period_start = line_before_pause and line_before_pause.date or self.prorata_date or self.first_depreciation_date
                try:
                    time_ratio = ((pause_date - depreciation_period_start).days) / (first_following.date - depreciation_period_start).days
                    new_line = self._insert_depreciation_line(line_before_pause, first_following.amount_total * time_ratio, _("Asset paused"), pause_date)
                    if pause_date <= fields.Date.today():
                        new_line.post()
                except ZeroDivisionError:
                    pass

            self.write({'state': 'paused'})
            self.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == asset_pause_type).unlink()
            self.message_post(body=_("Asset paused"))
        else:
            raise UserError(_("Trying to pause an asset without any future depreciation line"))

    #se modifican los onchange ya que la funcionalidad no es necesaria
    @api.onchange('account_depreciation_id')
    def _onchange_account_depreciation_id(self):
        print('override')

    @api.onchange('account_asset_id')
    def _onchange_account_asset_id(self):
        print('override')


    @api.onchange('account_depreciation_id', 'account_depreciation_expense_id')
    def _onchange_depreciation_account(self):
        print('override')

    def valorizate_asset_niff(self, valorization_value, date):
        def get_line(asset, amount, account):
            return (0, 0, {
                'name': asset.name,
                'account_id': account.id,
                # 'partner_id': self.company_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)],
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * asset.value_residual or 0.0,
            })

        disposal_date = date
        account_analytic_id = self.account_analytic_id
        analytic_tag_ids = self.analytic_tag_ids
        company_currency = self.company_id.currency_id
        current_currency = self.currency_id
        prec = company_currency.decimal_places

        # if any(self.depreciation_move_ids.filtered(lambda moves: moves.state == 'draft' and moves.asset_clasification == 'NIFF')):
        if valorization_value >0:
            account = self.profit_account_niff_id
        elif valorization_value < 0:
            account = self.loss_account_niff_id
        self.book_value_niff += valorization_value
        # self.acumulated_valorization_niff += valorization_value
        # self.method_number_niff = method_number

        line_datas = [(valorization_value, account), (-valorization_value, self.account_asset_id_niff)]
        vals = {
                'amount_total': abs(valorization_value),
                'asset_id': self.id,
                'ref': self.name + ': ' + (_('Valorization') if valorization_value > 0 else _('Losse')),
                'type': 'entry',
                'asset_remaining_value': 0,
                # 'asset_depreciated_value': max(self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'NIFF'), key=lambda x: x.date, default=self.env['account.move']).asset_depreciated_value,
                'asset_depreciated_value': 0,
                'date': disposal_date,
                'journal_id': self.journal_id_niff.id,
                'asset_clasification': 'valorizacion_niff' if valorization_value > 0 else 'desvalorizacion_niff',
                'line_ids': [get_line(self, amount, account) for amount, account in line_datas if account],
            }
        self.write({'depreciation_move_ids': [(0,0,vals)]})
        moves = self.depreciation_move_ids.filtered(lambda moves: moves.state == 'draft' and (moves.asset_clasification == 'valorizacion_niff' or moves.asset_clasification == 'desvalorizacion_niff'))
        for move in moves:
            move.action_post()
            # self.compute_depreciation_board()


    def valorizate_asset(self, valorization_value, date):
        def get_line(asset, amount, account):
            return (0, 0, {
                'name': asset.name,
                'account_id': account.id,
                # 'partner_id': self.company_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)],
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * asset.value_residual or 0.0,
            })

        disposal_date = date
        account_analytic_id = self.account_analytic_id
        analytic_tag_ids = self.analytic_tag_ids
        company_currency = self.company_id.currency_id
        current_currency = self.currency_id
        prec = company_currency.decimal_places

        # if any(self.depreciation_move_ids.filtered(lambda moves: moves.state == 'draft' and moves.asset_clasification == 'FISCAL')):
            # if valorization_value <0:
            #     account = self.profit_account_id
            #     sec_account = self.loss_account_id
            # elif valorization_value > 0:
        account = self.loss_account_id
        sec_account = self.profit_account_id
        # self.book_value += valorization_value
        # self.acumulated_valorization += valorization_value
        # self.method_number = method_number

        line_datas = [(valorization_value, account), (-valorization_value, sec_account)]
        vals = {
                'amount_total': abs(valorization_value),
                'asset_id': self.id,
                'ref': self.name + ': ' + (_('Valorization') if valorization_value > 0 else _('Losse')),
                'type': 'entry',
                'asset_remaining_value': 0,
                # 'asset_depreciated_value': max(self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'FISCAL'), key=lambda x: x.date, default=self.env['account.move']).asset_depreciated_value,
                'asset_depreciated_value': 0,
                'date': disposal_date,
                'journal_id': self.journal_id.id,
                'asset_clasification': 'valorizacion_fiscal' if valorization_value > 0 else 'desvalorizacion_fiscal',
                'line_ids': [get_line(self, amount, account) for amount, account in line_datas if account],
            }
        self.write({'depreciation_move_ids': [(0,0,vals)]})
        moves = self.depreciation_move_ids.filtered(lambda moves: moves.state == 'draft' and (moves.asset_clasification == 'valorizacion_fiscal' or moves.asset_clasification == 'desvalorizacion_fiscal'))
        for move in moves:
            move.action_post()
            # self.compute_depreciation_board()


    def modify_model(self, type, new_model_id, date):
        def get_line(asset, amount, account):
            return (0, 0, {
                'name': asset.name,
                'account_id': account.id,
                # 'partner_id': self.company_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * asset.value_residual or 0.0,
            })

        disposal_date = date or fields.Date.today()
        account_analytic_id = self.account_analytic_id
        analytic_tag_ids = self.analytic_tag_ids
        company_currency = self.company_id.currency_id
        current_currency = self.currency_id
        prec = company_currency.decimal_places
        
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.reversal_move_id and (x.asset_clasification == 'FISCAL' or x.asset_clasification == 'NIFF')).sorted(key=lambda l: l.date)
        last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].date) if posted_depreciation_move_ids else fields.Date.today()
        if last_depreciation_date.month >= date.month:  # in case we unpause the asset
            date = last_depreciation_date + relativedelta(months=+int(self.method_period))

        month_days = calendar.monthrange(date.year, date.month)[1]
        date = date.replace(day=month_days)

        first_depreciation_date = self.first_depreciation_date
        first_depreciation_date_niff = self.first_depreciation_date_niff
        self.first_depreciation_date = date
        self.first_depreciation_date_niff = date

        if type != 'BOTH':
            account = self.account_asset_id if type == 'FISCAL' else self.account_asset_id_niff
            new_account = new_model_id.account_asset_id if type == 'FISCAL' else new_model_id.account_asset_id_niff
            move_value = self.original_value  if type == 'FISCAL' else self.original_value_niff
            posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == type)
            already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids])
            account_depreciation = self.account_depreciation_id if type == 'FISCAL' else self.account_depreciation_id_niff
            new_account_depreciation = new_model_id.account_depreciation_id if type == 'FISCAL' else new_model_id.account_depreciation_id_niff
            if already_depreciated_amount != 0:
                line_datas = [(move_value, account), (-move_value, new_account), (-already_depreciated_amount,account_depreciation), (already_depreciated_amount,new_account_depreciation)]
            else:
                line_datas = [(move_value, account), (-move_value, new_account)]
            vals = {
                    'amount_total': abs(move_value),
                    'asset_id': self.id,
                    'ref': self.name + ': Cambio de Modelo ' + (_('NIFF') if type == 'NIFF' else _('FISCAL')),
                    'type': 'entry',
                    'asset_remaining_value': 0,
                    'asset_depreciated_value': 0,
                    'date': disposal_date,
                    'journal_id': self.journal_id_niff.id if type == 'NIFF' else self.journal_id.id,
                    'asset_clasification': _('NIFF_move') if type == 'NIFF' else _('FISCAL_move'),
                    'line_ids': [get_line(self, amount, account) for amount, account in line_datas if account],
                }
            self.write({'depreciation_move_ids': [(0,0,vals)]})
            if type == 'NIFF' and self.acumulated_valorization_niff != 0:
                account = self.account_asset_id_niff
                new_account = new_model_id.account_asset_id_niff
                move_value = self.acumulated_valorization_niff
                line_datas = [(-move_value, account), (move_value, new_account)]
                vals = {
                        'amount_total': abs(move_value),
                        'asset_id': self.id,
                        'ref': self.name + _(': Cambio de Modelo NIFF-avaluo'),
                        'type': 'entry',
                        'asset_remaining_value': 0,
                        'asset_depreciated_value': 0,
                        'date': disposal_date,
                        'journal_id': self.journal_id_niff.id,
                        'asset_clasification': _('NIFF_move'),
                        'line_ids': [get_line(self, amount, account) for amount, account in line_datas if account],
                    }
                self.write({'depreciation_move_ids': [(0,0,vals)]})      

            drepreciated_moves = len(self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == type))
            if type == 'NIFF':
                self.model_niff_id = new_model_id
                self._onchange_model_niff_id()
                if self.method_number_niff != 0:
                    actual_method_number = self.method_number_niff
                    if drepreciated_moves >= actual_method_number:
                        raise UserError(_('El numero de depreciaciones publicadas es mayor que el numero de depreciaciones en el nuevo modelo'))
                    self.method_number_niff = (actual_method_number - drepreciated_moves)
                    self.onchange_analytic_account_id_niff()
                    self.compute_depreciation_board()
                    self.method_number_niff = actual_method_number
                else:
                    self.onchange_analytic_account_id_niff()
                    self.compute_depreciation_board()
            elif type == 'FISCAL':
                self.model_id = new_model_id
                self._onchange_model_id()
                if self.method_number != 0:
                    actual_method_number = self.method_number
                    if drepreciated_moves >= actual_method_number:
                        raise UserError(_('El numero de depreciaciones publicadas es mayor que el numero de depreciaciones en el nuevo modelo'))
                    self.method_number = (actual_method_number - drepreciated_moves)
                    self.onchange_analytic_account_id()
                    self.compute_depreciation_board()
                    self.method_number = actual_method_number
                else:
                    self.onchange_analytic_account_id()
                    self.compute_depreciation_board()
        elif type == 'BOTH':
            if self.acumulated_valorization_niff != 0:
                account = self.account_asset_id_niff
                new_account = new_model_id.account_asset_id_niff
                move_value = self.acumulated_valorization_niff
                line_datas = [(move_value, account), (-move_value, new_account)]
                vals = {
                        'amount_total': abs(move_value),
                        'asset_id': self.id,
                        'ref': self.name + _(': Cambio de Modelo NIFF-avaluo'),
                        'type': 'entry',
                        'asset_remaining_value': 0,
                        'asset_depreciated_value': 0,
                        'date': disposal_date,
                        'journal_id': self.journal_id_niff.id,
                        'asset_clasification': _('NIFF_move'),
                        'line_ids': [get_line(self, amount, account) for amount, account in line_datas if account],
                    }
                self.write({'depreciation_move_ids': [(0,0,vals)]})
                
            account = self.account_asset_id
            new_account = new_model_id.account_asset_id
            move_value = self.original_value
            posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'FISCAL').sorted(key=lambda l: l.date)
            already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids])
            account_depreciation = self.account_depreciation_id
            new_account_depreciation = new_model_id.account_depreciation_id
            if already_depreciated_amount != 0:
                line_datas = [(move_value, account), (-move_value, new_account), (-already_depreciated_amount,account_depreciation), (already_depreciated_amount,new_account_depreciation)]
            else:
                line_datas = [(move_value, account), (-move_value, new_account)]
            vals = {
                    'amount_total': abs(move_value),
                    'asset_id': self.id,
                    'ref': self.name + ': Cambio de Modelo FISCAL',
                    'type': 'entry',
                    'asset_remaining_value': 0,
                    'asset_depreciated_value': 0,
                    'date': disposal_date,
                    'journal_id': self.journal_id.id,
                    'asset_clasification': 'FISCAL_move',
                    'line_ids': [get_line(self, amount, account) for amount, account in line_datas if account],
                }
            self.write({'depreciation_move_ids': [(0,0,vals)]})
            account = self.account_asset_id_niff
            new_account = new_model_id.account_asset_id_niff
            move_value = self.original_value_niff
            posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'NIFF').sorted(key=lambda l: l.date)
            already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids])
            account_depreciation = self.account_depreciation_id_niff
            new_account_depreciation = new_model_id.account_depreciation_id_niff
            if already_depreciated_amount != 0:
                line_datas = [(move_value, account), (-move_value, new_account), (-already_depreciated_amount, account_depreciation), (already_depreciated_amount, new_account_depreciation)]
            else:
                line_datas = [(move_value, account), (-move_value, new_account)]
            vals = {
                    'amount_total': abs(move_value),
                    'asset_id': self.id,
                    'ref': self.name + ': Cambio de Modelo NIFF',
                    'type': 'entry',
                    'asset_remaining_value': 0,
                    'asset_depreciated_value': 0,
                    'date': disposal_date,
                    'journal_id': self.journal_id_niff.id,
                    'asset_clasification': 'NIFF_move',
                    'line_ids': [get_line(self, amount, account) for amount, account in line_datas if account],
                }
                
            self.write({'depreciation_move_ids': [(0,0,vals)]})
            self.model_id = new_model_id
            self._onchange_model_id()
            if self.method_number:
                drepreciated_moves = len(self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'FISCAL'))
                actual_method_number = self.method_number
                if drepreciated_moves >= actual_method_number:
                    raise UserError(_('El numero de depreciaciones publicadas es mayor que el numero de depreciaciones en el nuevo modelo'))
                self.method_number = actual_method_number - drepreciated_moves
                self.onchange_analytic_account_id()
                self.compute_depreciation_board()
                self.method_number = actual_method_number
            else:
                self.onchange_analytic_account_id()
                self.compute_depreciation_board()
            self.model_niff_id = new_model_id
            self._onchange_model_niff_id()
            if self.method_number_niff:
                drepreciated_moves_niff = len(self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and x.asset_clasification == 'NIFF'))
                actual_method_number_niff = self.method_number_niff
                if drepreciated_moves_niff >= actual_method_number_niff:
                    raise UserError(_('El numero de depreciaciones publicadas es mayor que el numero de depreciaciones en el nuevo modelo'))
                self.method_number_niff = actual_method_number_niff - drepreciated_moves_niff
                self.onchange_analytic_account_id_niff()
                self.compute_depreciation_board_niff()
                self.method_number_niff = actual_method_number_niff
            else:
                self.onchange_analytic_account_id_niff()
                self.compute_depreciation_board_niff()
        self.first_depreciation_date = first_depreciation_date
        self.first_depreciation_date_niff = first_depreciation_date_niff
        moves = self.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and (x.asset_clasification == 'NIFF_move' or x.asset_clasification == 'FISCAL_move'))
        for move in moves:
            move.action_post()

    def adjust_values(self, method_number, adjust_type, original_value, initial_date, adjust_account):
        def get_line(amount, account):
            return (0, 0, {
                'name': self.name,
                'account_id': account.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'analytic_account_id': self.account_analytic_id.id,
                'analytic_tag_ids': False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * self.value_residual or 0.0,
            })

        company_currency = self.company_id.currency_id
        current_currency = self.currency_id
        prec = company_currency.decimal_places
        dif_orig_value = 0

        # if self.original_value == original_value:
        #     return
        if adjust_type == 'depreciation':
            self.method_number = method_number
        elif adjust_type == 'value':
            dif_orig_value = original_value - self.original_value
            self.original_value = original_value
        elif adjust_type == 'initial_date':
            original_initial_date = self.first_depreciation_date
            dif_date = relativedelta(original_initial_date, initial_date) if original_initial_date > initial_date else relativedelta(initial_date,original_initial_date)
            resta = original_initial_date - initial_date
            self.first_depreciation_date = initial_date
            

        self.ensure_one()
        amount_change_ids = self.depreciation_move_ids.filtered(lambda x: x.asset_value_change and not x.reversal_move_id and x.asset_clasification == 'FISCAL').sorted(key=lambda l: l.date)
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id and x.asset_clasification == 'FISCAL').sorted(key=lambda l: l.date)
        already_depreciated_amount = sum([m.amount_total for m in posted_depreciation_move_ids]) or 0
        if already_depreciated_amount == 0:
            return
        depreciation_number = self.method_number
        if self.prorata:
            depreciation_number += 1
        starting_sequence = 0
        amount_to_depreciate = self.original_value
        depreciation_date = self.first_depreciation_date
        # if we already have some previous validated entries, starting date is last entry + method period
        # if posted_depreciation_move_ids and posted_depreciation_move_ids[-1].date:
        #     last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].date)
        #     if last_depreciation_date > depreciation_date:  # in case we unpause the asset
        #         depreciation_date = last_depreciation_date + relativedelta(months=+int(self.method_period))
        commands = [(2, line_id.id, False) for line_id in self.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification == 'FISCAL')]
        [commands.append((2, line_id.id, False)) for line_id in self.depreciation_move_ids.filtered(lambda x: x.state == 'draft' and x.asset_clasification in ('valorizacion_fiscal','desvalorizacion_fiscal'))]
        newlines = self._recompute_board(depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, 0, amount_change_ids)
        depre_proyectada =  newlines[len(posted_depreciation_move_ids)-1]['asset_depreciated_value']
        if adjust_type in ('value','depreciation'):
            del(newlines[0:len(posted_depreciation_move_ids)])
                
        newline_vals_list = []
        for newline_vals in newlines:
            # no need of amount field, as it is computed and we don't want to trigger its inverse function
            del(newline_vals['amount_total'])
            newline_vals['asset_clasification'] = "FISCAL"
            newline_vals_list.append(newline_vals)
        #movimiento de ajuste
        
        cuota = (newline_vals_list[0]['asset_remaining_value'] - newline_vals_list[1]['asset_remaining_value'])
        adjust_value = float_round(depre_proyectada - already_depreciated_amount, precision_rounding=self.currency_id.rounding)
        depreciated_value = already_depreciated_amount + adjust_value + cuota
        remaining_value = amount_to_depreciate - depreciated_value
        value_residual = float_round(remaining_value, precision_rounding=self.currency_id.rounding)

        if adjust_type == 'depreciation':
            vals = self.env['account.move']._prepare_move_for_asset_depreciation({
                        'amount': adjust_value + cuota,
                        'asset_id': self,
                        'move_ref': 'Ajuste de valor del activo (' + str(len(posted_depreciation_move_ids)+1) +'/' + str(self.method_number) + ')',
                        'date': newline_vals_list[0]['date'],
                        'asset_remaining_value': value_residual,
                        'asset_depreciated_value': depreciated_value,
                    })
            vals['negative_amount'] = True if (adjust_value + cuota) < 0 else False
            new_move = self.env['account.move'].create(vals)
            # new_move.amount_total = adjust_value
            # new_move.auto_post = False
            # new_move.post()
            del(newline_vals_list[0])
        elif adjust_type == 'value':
            line_datas = [(-dif_orig_value,self.account_asset_id),(dif_orig_value,adjust_account)]
            vals = {
                'amount_total': dif_orig_value,
                'asset_id': self.id,
                'ref': 'Ajuste de valor del activo' + (' +' if dif_orig_value >= 0 else ' -'),
                'asset_remaining_value': 0,
                'asset_depreciated_value': 0,
                'date': newline_vals_list[0]['date'],
                'asset_clasification': 'valorizacion_fiscal' if dif_orig_value >= 0 else 'desvalorizacion_fiscal',
                'journal_id': self.journal_id.id,
                'line_ids': [get_line(amount, account) for amount, account in line_datas if account],
            }
            new_move = self.env['account.move'].create(vals)
            new_move.post()
            vals = self.env['account.move']._prepare_move_for_asset_depreciation({
                'amount': adjust_value + cuota,
                'asset_id': self,
                'move_ref': 'Ajuste de valor del activo (' + str(len(posted_depreciation_move_ids)+1) +'/' + str(self.method_number) + ')',
                'date': newline_vals_list[0]['date'],
                'asset_remaining_value': value_residual,
                'asset_depreciated_value': depreciated_value,
            })
            vals['negative_amount'] = True if (adjust_value + cuota) < 0 else False
            new_move = self.env['account.move'].create(vals)
            # new_move.auto_post = False
            # new_move.post()
            #self.value_residual = value_residual
            del(newline_vals_list[0])
        elif adjust_type == 'initial_date':
            dif_period = 0
            if self.method_period == '1':
                dif_period = relativedelta(original_initial_date, initial_date).months if original_initial_date > initial_date else relativedelta(initial_date,original_initial_date).months
            elif self.method_period == '12':
                dif_period = relativedelta(original_initial_date, initial_date).years if original_initial_date > initial_date else relativedelta(initial_date,original_initial_date).years
            
            if initial_date < original_initial_date:
                for i in range(0,dif_period):
                    day = newline_vals_list[i]['date'].day
                    month = newline_vals_list[i]['date'].month
                    year = newline_vals_list[i]['date'].year
                    newline_vals_list[i]['ref'] = 'Ajuste Fecha (' + str(day) + '/' + str(month) + '/' + str(year) + ').'
                    newline_vals_list[i]['date'] = fields.Date.today()
                    newline_vals_list[i]['asset_depreciated_value'] = newline_vals_list[i+len(posted_depreciation_move_ids)]['asset_depreciated_value']
                    newline_vals_list[i]['asset_remaining_value'] = newline_vals_list[i+len(posted_depreciation_move_ids)]['asset_remaining_value']
                    new_move = self.env['account.move'].create(newline_vals_list[i])
                    new_move.post()
                del(newline_vals_list[0:dif_period + len(posted_depreciation_move_ids)])
            else:
                del(newline_vals_list[0:len(posted_depreciation_move_ids)])

        new_moves = self.env['account.move'].create(newline_vals_list)
        for move in new_moves:
            commands.append((4, move.id))
        self.write({'depreciation_move_ids': commands})
            


        

    def action_adjust_values(self):
        """ Returns an action opening the adjust values wizard.
            override to let modify multiple assets
        """
        
        # self.ensure_one()
        new_wizard = self.env['asset.adjust.depreciation.wizard'].create({
            'asset_id': self.id,
            'method_number': self.method_number,
            'original_value': self.original_value,
            'date': self.first_depreciation_date,
        })
        return {
            'name': _('Adjust Values'),
            'view_mode': 'form',
            'res_model': 'asset.adjust.depreciation.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
            'context': self.env.context,
        }

    def action_asset_modify(self):
        """ Returns an action opening the asset modification wizard.
            override to let modify multiple assets
        """
        
        # self.ensure_one()
        new_wizard = self.env['asset.modify'].create({
            'asset_id': self.id,
        })
        return {
            'name': _('Modify Asset'),
            'view_mode': 'form',
            'res_model': 'asset.modify',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
            'context': self.env.context,
        }


    def action_asset_valorizate(self):
        """ Returns an action opening the asset modification wizard.
            override to let modify multiple assets
        """
        # self.ensure_one()
        if not self.profit_account_id or not self.loss_account_id:
            raise UserError(_("Por favor seleccione cuenta para ganancias y perdidas"))
        new_wizard = self.env['account.asset.valorization'].create({
            'asset_id': self.id,
        })
        return {
            'name': _('Valorizate Asset'),
            'view_mode': 'form',
            'res_model': 'account.asset.valorization',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
            'context': self.env.context,
        }


    def action_asset_modify_model(self):
        """ Returns an action opening the asset model modification  wizard.
        """
        # self.ensure_one()
        new_wizard = self.env['account.asset.modify.model'].create({
            'asset_id': self.id,
            'actual_niff_model_id': self.model_niff_id.id,
            'actual_fiscal_model_id': self.model_id.id,
        })
        return {
            'name': _('Edicion del modelo del activo'),
            'view_mode': 'form',
            'res_model': 'account.asset.modify.model',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
            'context': self.env.context,
        }


    def action_post_deferred_revenue(self):
        """ Returns an action opening the asset model modification  wizard.
        """
        # self.ensure_one()
        new_wizard = self.env['post.deferred.revenue'].create({
            'asset_id': self.id,
            'unpublished_entries': len(self.depreciation_move_ids.filtered(lambda x: not x.reversal_move_id and x.asset_clasification == 'FISCAL' and x.state == 'draft')),
        })
        return {
            'name': _('Publicacion de Asientos'),
            'view_mode': 'form',
            'res_model': 'post.deferred.revenue',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
            'context': self.env.context,
        }