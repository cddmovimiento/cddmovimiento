# -*- coding: utf-8 -*-

from odoo import api, fields, models
class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    hourmeter_count = fields.Integer(compute="_compute_count_all_hourmeter", string='Horómetro')
    hourmeter = fields.Float(compute='_get_hourmeter', inverse='_set_hourmeter', string='Último horómetro', help='Horómetro del vehículo en el momento de este registro')
    hourmeter_unit = fields.Selection([
        ('hours', 'hrs'),
        ('minutes', 'min')
    ], 'Unidad de horómetro', default='hours', help='Unidad del horómetro', required=True)

    def _get_hourmeter(self):
        FleetVehicalHourmeter = self.env['fleet.vehicle.hourmeter']
        for record in self:
            vehicle_hourmeter = FleetVehicalHourmeter.search([('vehicle_id', '=', record.id)], limit=1, order='value desc')
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

