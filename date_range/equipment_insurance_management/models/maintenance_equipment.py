# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AssetsInsuranceLine(models.Model):
    _name = "assets.insurance.line"
    _description = 'lineas de activos en el seguro'

    insurance_ids = fields.Many2one(
        'maintenance.equipment.insurance',
        string='Seguro'
    )

    prima = fields.Float(string='prima')
    porcentaje_iva = fields.Float(string='% IVA')
    iva = fields.Float(string='IVA', compute='_compute_iva')
    fecha_entrega = fields.Date(string='Fecha de entrega')
    city_id = fields.Many2one('res.city', string='Ciudad entrega')
    fecha_inicio = fields.Date(string='Fecha de inicio', help='Fecha de inicio del seguro')
    fecha_fin = fields.Date(string='Fecha de fin', help='Fecha de fin del seguro')
    plan = fields.Char(string='Plan')

    asset_id = fields.Many2one('account.asset',
                               string='Activo')
    partner_id = fields.Many2one('res.partner', related='asset_id.partner_id', store=True)

    @api.depends('prima', 'porcentaje_iva')
    def _compute_iva(self):
        for line in self:
            line.iva = line.porcentaje_iva * line.prima / 100

    # @api.multi
    def action_create_insurance(self):
        compose_form_id = self.env.ref("equipment_insurance_management.view_equipment_insurance_form_view").id
        ctx = {
            'default_name': self.name,
            'default_equipment_id': self.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.equipment.insurance',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'current',
            'context': ctx,
        }

    # @api.multi
    def action_button_insurance(self):
        self.ensure_one()
        action = self.env.ref("equipment_insurance_management.action_equipment_insurance_view").read([])[0]
        action['domain'] = [('equipment_id', '=', self.id)]
        return action


class SiniestrosAssetsLine(models.Model):
    _name = "assets.siniestros.line"
    _description = 'lineas de siniestros en el seguro'


    siniestros_id = fields.Many2one(
        'maintenance.equipment.insurance',
        string='Seguro'
    )
    activos_seguro_ids = fields.One2many('account.asset', compute="_compute_domain_assets")
    asset_id = fields.Many2one('account.asset',
                               string='Activo',  domain="[('id', 'in', activos_seguro_ids)]")
    fecha_siniestro = fields.Date(string='Fecha', required=True)
    fecha_reclamacion = fields.Date(string='Fecha reclamación')
    canal_reclamacion = fields.Char(string='canal reclamacion')
    novedad_id = fields.Many2one('novedad.seguro', string='Novedad', ondelete='restrict')
    city_id = fields.Many2one('res.city', string='Ciudad siniestro')
    city_reclamacion_id = fields.Many2one('res.city', string='Ciudad reclamación')
    tipo_siniestro = fields.Selection(selection=[
                                    ('dano', 'Daño'),
                                    ('hurto', 'Hurto')
                                ], string='Tipo de siniestro')
    note = fields.Text('Descripcion hechos')

    @api.depends('siniestros_id.equipment_ids')
    def _compute_domain_assets(self):
        for rec in self:
            record = self.env['account.asset']
            for asset in rec.siniestros_id.equipment_ids:
                if asset.asset_id:
                    record += asset.asset_id
            rec.activos_seguro_ids += record




class NovedadesSeguros(models.Model):
    _name = 'novedad.seguro'
    _description = 'novedades en los seguros'

    name = fields.Char(string='Novedad')
    active = fields.Boolean(string='Activo', default=True)


class MaintenanceEquipment(models.Model):
    _inherit = "account.asset"

    @api.depends('insurance_ids')
    def _compute_is_create_insurance(self):
        for rec in self:
            insurance_ids = self.env['maintenance.equipment.insurance'].search([('asset_ids', 'in', [self.id])])
            if len(insurance_ids) > 0:
                rec.is_create_insurance = True
            else:
                rec.is_create_insurance = False

    insurance_ids = fields.Many2many(
        'maintenance.equipment.insurance',
        'asset_id',
        string='Seguro'
    )
    is_create_insurance = fields.Boolean(
        string='¿Se crea Seguro?',
        compute='_compute_is_create_insurance',
        copy=False
    )

    residual_value = fields.Float(string='Valor residual %')

    # @api.multi
    def action_create_insurance(self):
        compose_form_id = self.env.ref("equipment_insurance_management.view_equipment_insurance_form_view").id
        ctx = {
            'default_name': self.name,
            'default_asset_ids': [self.id],
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'maintenance.equipment.insurance',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'current',
            'context': ctx,
        }

    # @api.multi
    def action_button_insurance(self):
        self.ensure_one()
        action = self.env.ref("equipment_insurance_management.action_equipment_insurance_view").read([])[0]
        action['domain'] = [('asset_ids', 'in', self.id)]
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
