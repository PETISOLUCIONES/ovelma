# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class InventoryLine(models.Model):
    _inherit = "stock.quant"

    adjustment_cost = fields.Monetary(
        string="Adjustment cost", compute="_compute_adjustment_cost", store=True
    )

    @api.depends("inventory_diff_quantity")
    def _compute_adjustment_cost(self):
        for record in self:
            record.adjustment_cost = (
                record.inventory_diff_quantity * record.product_id.standard_price
            )
