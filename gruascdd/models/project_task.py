# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = "project.task"

    employee_ids = fields.Many2many(
        "hr.employee",
        string="Empleados",
        store=True
    )

    pozo = fields.Char(
        "Pozo"
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['editable'] = True
        
        tasks = super(ProjectTask, self).create(vals_list)

        for task in tasks:
            if task.sale_order_id:
                total_hours = sum(line.product_uom_qty for line in task.sale_order_id.order_line)
                task.allocated_hours = total_hours * 2

        return tasks

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
            if line.tercer_ayudante_id:
                # Registro tercer ayudante
                timesheet_ids.append((0, 0, {
                    'date': line.date_init.date(),
                    'employee_id': line.tercer_ayudante_id.id,
                    'name': line.comment,
                    'unit_amount': line.delta,
                }))

            # Se podrán enviar al módulo de flotas desde la bitácora siempre que el registro haya sido creado en Odoo
            '''if line.vehicle_id and line.origen != 'tablet':
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

                # Crea registro de gasolina en el vehículo
                self.env["fleet.vehicle.gas"].create({
                    "date": line.date_end,
                    "value": line.gasolina,
                    "vehicle_id": line.vehicle_id.id,
                    "driver_employee_id": line.gruero_id.id,
                    "driver_id": line.gruero_id.address_home_id.id,
                })'''
                
        self.timesheet_ids = timesheet_ids

        self.editable = False
