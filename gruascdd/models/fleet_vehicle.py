# -*- coding: utf-8 -*-

from odoo import api, fields, models
class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    hourmeter_count = fields.Integer(compute="_compute_count_all_hourmeter", string='Horómetro ')
    hourmeter = fields.Float(compute='_get_hourmeter', inverse='_set_hourmeter', string='Último horómetro', help='Horómetro del vehículo en el momento de este registro')
    
    gas_count = fields.Integer(compute="_compute_count_all_gas_carge", string='Diésel')
    gas = fields.Float(compute='_get_gas', inverse='_set_gas', string='Última carga diésel', help='Carga de diésel al vehículo en el momento de este registro')
    
    hourmeter_unit = fields.Selection([
        ('hours', 'hrs'),
        ('minutes', 'min')
    ], 'Unidad de horómetro ', default='hours', help='Unidad del horómetro', required=True)

    gas_unit = fields.Selection([
        ('litros', 'l')
    ], 'Unidad de Diésel', default='litros', help='Unidad de diesel', required=True)

    def _get_odometer(self):
        super()._get_odometer()
        
        FleetVehicalOdometer = self.env['fleet.vehicle.odometer']
        for record in self:
            vehicle_odometer = FleetVehicalOdometer.search([('vehicle_id', '=', record.id)], limit=1, order='date desc')
            if vehicle_odometer:
                record.odometer = vehicle_odometer.value
            else:
                record.hourmeter = 0
                
    def _get_hourmeter(self):
        FleetVehicalHourmeter = self.env['fleet.vehicle.hourmeter']
        for record in self:
            vehicle_hourmeter = FleetVehicalHourmeter.search([('vehicle_id', '=', record.id)], limit=1, order='date desc')
            if vehicle_hourmeter:
                record.hourmeter = vehicle_hourmeter.value
            else:
                record.hourmeter = 0

    def _set_hourmeter(self):
        for record in self:
            if record.hourmeter:
                date = fields.Date.context_today(record)
                data = {
                    'value': record.hourmeter,
                    'date': date,
                    'vehicle_id': record.id,
                    'unit': record.hourmeter_unit,

                }
                self.env['fleet.vehicle.hourmeter'].create(data)

    def _get_gas(self):
        fleetVehicalGas = self.env['fleet.vehicle.gas']
        for record in self:
            vehicle_gas = fleetVehicalGas.search([('vehicle_id', '=', record.id)], limit=1, order='date desc')
            if vehicle_gas:
                record.gas = vehicle_gas.value
            else:
                record.gas = 0

    def _set_gas(self):
        for record in self:
            if record.gas:
                date = fields.Date.context_today(record)
                data = {
                    'value': record.gas,
                    'date': date,
                    'vehicle_id': record.id,
                    'unit': record.gas_unit,

                }
                self.env['fleet.vehicle.gas'].create(data)
                
    def _compute_count_all_hourmeter(self):
        Hourmeter = self.env['fleet.vehicle.hourmeter']
        for record in self:
            record.hourmeter_count = Hourmeter.search_count([('vehicle_id', '=', record.id)])

    def return_action_to_open_hourmeter(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('gruascdd.%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_vehicle_id=self.id, group_by=False),
                domain=[('vehicle_id', '=', self.id)]
            )
            return res
        return False

    def _compute_count_all_gas_carge(self):
        gas = self.env['fleet.vehicle.gas']
        for record in self:
            record.gas_count = gas.search_count([('vehicle_id', '=', record.id)])

    def return_action_to_open_gas(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('gruascdd.%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_vehicle_id=self.id, group_by=False),
                domain=[('vehicle_id', '=', self.id)]
            )
            return res
        return False

