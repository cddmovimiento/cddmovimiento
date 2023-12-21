# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTask(models.Model):
    _inherit = "project.task"

    employee_ids = fields.Many2many(
        "hr.employee",
        string="Empleados",
        store=True
    )

    pozo = fields.Char(
        "Pozo",
        required=True
    )

    model_fleet_id = fields.Many2one(
        comodel_name="fleet.vehicle.model",
        string="Modelo de la grúa",
        store=True,
    )

    binnacle_ids = fields.One2many(
        "project.binnacle",
        "parent_id",
        string="Bitácora"
    )

    @api.model
    def create(self, vals):
        result = super(ProjectTask, self).create(vals)

        if result.sale_order_id:
            total_hours = 0
            for line in result.sale_order_id.order_line:
                total_hours += line.product_uom_qty

            result.planned_hours = total_hours * 2
        return result