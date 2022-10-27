# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpProductionReport(models.AbstractModel):
    _name = 'report.mrp_production_report.report_mrp_production_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        production_ids = self.env['mrp.production'].browse(docids)

        valor = {
            'doc_model': 'mrp.production',
            'lines': self.get_lines(production_ids),
        }

        return valor

    @api.model
    def get_lines(self, production_ids):
        """
        , resume=True
        Tomas las ventas sale_order
        Busca todos los centros de produccion y los identifica
        Busca las producciones segun centros de produccion
        Busca ordenes segun
        """

        if len(production_ids) > 1:
            production_ids = production_ids[0]

        sale_id = self.env['sale.order'].search([
                            ('name', '=', production_ids.origin)
                        ])

        prod_ids = self.env['mrp.production'].search([
                            ('origin', 'ilike', production_ids.origin and production_ids.origin or 'XxXxXxYy'),
                            ('state', 'not in', ['cancel'])
                        ])

        if not prod_ids:
            prod_ids = production_ids

        """
        stock_move_ids = self.env['stock.move'].search([
                            ('raw_material_production_id','in', prod_ids.ids)
                        ])
        """

        operation = []
        materials = []

        for prod_id in prod_ids:
            if prod_id.state in ['cancel']:
                continue
            for material in prod_id.move_raw_ids:
                if material.state in ['cancel']:
                    continue
                operation_name = material.operation_id and material.operation_id.name.strip().upper() or 'Indefinido'
                if operation_name not in operation:
                    operation.append(operation_name)
                    materials.append({
                        'operation_id': operation_name,
                        'mp': []
                    })

                operation_id = next(
                    (x for i, x in enumerate(materials)
                        if x["operation_id"] == operation_name), None
                )

                mp = next(
                    (x for i, x in enumerate(operation_id['mp'])
                        if x["product_id"] == material.product_id
                    ), None
                )

                if mp:
                    mp['ordered_qty'] += material.product_uom_qty
                    if material.raw_material_production_id not in mp['production_ids']:
                        mp['production_ids'] += material.raw_material_production_id
                else:
                    operation_id['mp'].append({
                        'product_id': material.product_id,
                        'ordered_qty': material.product_uom_qty,
                        'production_ids': material.raw_material_production_id,
                        'operation_id': operation_name,
                        'product_uom': material.product_uom,
                    })
        if materials:
            for m in materials:
                m = sorted(m['mp'], key=lambda i: i['product_id'].id)
            materials = sorted(materials, key=lambda i: i['operation_id'])

        result = [{
            'sale': sale_id,
            'production': prod_ids,
            'materials': materials
        }]
        return result
