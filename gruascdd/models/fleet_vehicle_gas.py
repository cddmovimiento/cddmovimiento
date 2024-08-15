# -*- coding: utf-8 -*-
from odoo import api, fields, models

class FleetVehicleGas(models.Model):
    _name = 'fleet.vehicle.gas'
    _description = 'Diesel log for a vehicle'
    _order = 'date desc'

    name = fields.Char(compute="_compute_vehicle_log_name", store=True)
    date = fields.Date(default=fields.Date.context_today)
    value = fields.Float("Diesel Value", group_operator="max")
    vehicle_id = fields.Many2one("fleet.vehicle", 'Vehicle', required=True)
    unit = fields.Selection(related="vehicle_id.gas_unit", string="Unit", readonly=True)
    driver_id = fields.Many2one(related="vehicle_id.driver_id", string="Driver", readonly=False)
    driver_employee_id = fields.Many2one(related="vehicle_id.driver_employee_id", string="Conductor(Empleado)", readonly=False)
    binnacle_id = fields.Integer(string='Bitácora',store=True, readonly=True)
    task_name = fields.Char("Servicio", store=True, readonly=True)
    folio = fields.Char("Folio", store=True, readonly=True)


    @api.depends("vehicle_id", "date")
    def _compute_vehicle_log_name(self):
        for record in self:
            name = record.vehicle_id.name
            if not name:
                name = str(record.date)
            elif record.date:
                name += ' / ' + str(record.date)
            record.name = name

    @api.onchange("vehicle_id")
    def _onchange_vehicle(self):
        if self.vehicle_id:
            self.unit = self.vehicle_id.gas_unit