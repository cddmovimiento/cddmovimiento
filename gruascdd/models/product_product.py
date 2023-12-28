# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    in_sale_order = fields.Integer(
        "in_sale_order",
        compute="_compute_in_sale_order",
        search="_search_in_sale_order"
    )

    @api.depends("name")
    def _compute_in_sale_order(self):
        self.in_sale_order=1

    @api.model
    def _search_in_sale_order(self, operator, value):
        if operator == "=":
            task = self.env["project.task"].search([("id", "=", value)])
            order = self.env["sale.order"].search([("id", "=", task.sale_order_id.id)])
            if order:
                products = []
                for line in order.order_line:
                    if line.product_id.id not in products:
                        products.append(line.product_id.id)
                return [("id", "in", products)]
            else:
                return False
        else:
            return False