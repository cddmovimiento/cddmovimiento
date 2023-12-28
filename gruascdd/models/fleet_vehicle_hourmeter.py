# -*- coding: utf-8 -*-
from odoo import api, fields, models
class FleetVehicleHourmeter(models.Model):
    _name = 'fleet.vehicle.hourmeter'
    _description = 'Hourmeter log for a vehicle'
    _order = 'date desc'

    name = fields.Char(compute="_compute_vehicle_log_name", store=True)
    date = fields.Date(default=fields.Date.context_today)
    value = fields.Float("Horometer Value", group_operator="max")
    vehicle_id = fields.Many2one("fleet.vehicle", 'Vehicle', required=True)
    unit = fields.Selection(related="vehicle_id.hourmeter_unit", string="Unit", readonly=True)
    driver_id = fields.Many2one(related="vehicle_id.driver_id", string="Driver", readonly=False)
    driver_employee_id = fields.Many2one(related="vehicle_id.driver_employee_id", string="Conductor(Empleado)", readonly=False)


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
            self.unit = self.vehicle_id.hourmeter_unit
