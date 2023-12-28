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

    editable = fields.Boolean("Editable", default=True)

    @api.model
    def create(self, vals):
        self.editable = True
        result = super(ProjectTask, self).create(vals)

        if result.sale_order_id:
            total_hours = 0
            for line in result.sale_order_id.order_line:
                total_hours += line.product_uom_qty

            result.planned_hours = total_hours * 2
        return result

    def action_fsm_validate(self):
        super().action_fsm_validate()

        timesheet_ids = []

        for line in self.binnacle_ids:
            if line.gruero_id:
                # Registro Gruero
                timesheet_ids.append((0, 0, {
                    'date': line.date_init.date(),
                    'employee_id': line.gruero_id.id,
                    'name': line.comment,
                    'unit_amount': line.delta,
                }))
            if line.ayudante_id:
                # Registro Ayudante
                timesheet_ids.append((0, 0, {
                    'date': line.date_init.date(),
                    'employee_id': line.ayudante_id.id,
                    'name': line.comment,
                    'unit_amount': line.delta,
                }))
            if line.vehicle_id:
                # Crea registro del Odómetro en el vehículo
                self.env["fleet.vehicle.odometer"].create({
                    "date": line.date_end,
                    "value": line.odometer_end,
                    "vehicle_id": line.vehicle_id.id,
                    "driver_employee_id": line.gruero_id.id,
                    "driver_id": line.gruero_id.address_home_id.id,
                })
                # Crea registro del Horómetro en el vehículo
                self.env["fleet.vehicle.hourmeter"].create({
                    "date": line.date_end,
                    "value": line.hourmeter_end,
                    "vehicle_id": line.vehicle_id.id,
                    "driver_employee_id": line.gruero_id.id,
                    "driver_id": line.gruero_id.address_home_id.id,
                })

        self.timesheet_ids = timesheet_ids

        self.editable = False
