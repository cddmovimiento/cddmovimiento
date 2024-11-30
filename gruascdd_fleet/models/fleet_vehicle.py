# -*- coding: utf-8 -*-

from odoo import api, fields, models
class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    mantenimiento_A = fields.Float(string="Mantenimiento 400 ", default=400)
    mantenimiento_B = fields.Float(string="Mantenimiento 400  ", default=1600)
    mantenimiento_C = fields.Float(string="Mantenimiento 400   ", default=4000)
    
    horometro_control_4000 = fields.Float(string='Mamtenimiento Horómetro 4,000')
    horometro_control_1600 = fields.Float(string='Mantenimiento Horómetro 1,600')
    #send_email = fields.Char('Enviar a')
    fleet_services_config_id = fields.Many2one(comodel_name='fleet.services.config', string='Servicios')
    ultimate_service = fields.Float(string='Último servicio')
    
    start_hourmeter_unit = fields.Selection([
        ('hours', 'hrs'),
        ('minutes', 'min')
    ], 'Unidad de horómetro', default='hours', help='Unidad del horómetro', required=True)

    notification_count = fields.Integer(compute="_compute_count_notification", string='Notificaciones')
    
    def _compute_count_notification(self):
        notification = self.env['fleet.maintenance.notifications']
        for record in self:
            record.notification_count = notification.search_count([('vehicle_id', '=', record.id)])
            
    def return_action_to_open_notifications(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id(
            'gruascdd_fleet.action_fleet_maintenance_notifications_act_window')
        res.update(
            context=dict(self.env.context, default_vehicle_id=self.id, group_by=False),
            domain=[('vehicle_id', '=', self.id)]
        )
        return res

    def ir_cron_service_seven_days(self):

        vehicles = self.env['fleet.vehicle'].search([('id', '>', 0)])

        for v in vehicles:
            services_type = self.env['fleet.service.type'].search([('name', '=', 'Servicio de mantenimiento'),], limit=1)

            services_config = self.env['fleet.services.config'].search([
                ('quantity', '=', 7),
                ('type_range', '=', 'days')
            ])

            self.env['fleet.vehicle.log.services'].create({
                'service_type_id': services_type.id if services_type else False,
                'vehicle_id': v.id,
                'type_service_id': services_config.id if services_config else False,
            })    

    def ir_cron_service_one_days(self):

        vehicles = self.env['fleet.vehicle'].search([ ('id', '>', 0)])

        for v in vehicles:
            services_type = self.env['fleet.service.type'].search([('name', '=', 'Servicio de mantenimiento'),], limit=1)

            services_config = self.env['fleet.services.config'].search([
                ('quantity', '=', 1),
                ('type_range', '=', 'days')
            ])

            self.env['fleet.vehicle.log.services'].create({
                'service_type_id': services_type.id if services_type else False,
                'vehicle_id': v.id,
                'type_service_id': services_config.id if services_config else False,
            })

    def _services_vehicle(self):
        vehicles = self.env['fleet.vehicle'].search([('id', '>', 0)])

        for v in vehicles:
            dff = v.hourmeter - v.ultimate_service
            if dff >= v.mantenimiento_A:
                v.ultimate_service = v.hourmeter

                # create service 400 ============================================
                services_type = self.env['fleet.service.type'].search([
                    ('name', '=', 'Servicio de mantenimiento'),
                ], limit=1)

                services_config = self.env['fleet.services.config'].search([
                    ('quantity', '=', v.mantenimiento_A),
                    ('type_range', '=', 'hours'),
                ])

                self.env['fleet.vehicle.log.services'].create({
                    'service_type_id': services_type.id if services_type else False,
                    'vehicle_id': v.id,
                    'type_service_id': services_config.id if services_config else False,
                })
                v.horometro_control_1600 += dff
                v.horometro_control_4000 += dff
                # create service 400 ============================================

                # if v.horometro_control += 400:
                #     pass

                if v.horometro_control_1600 >= v.mantenimiento_B:
                    # create service 1600
                    services_config = self.env['fleet.services.config'].search([
                        ('quantity', '=', v.mantenimiento_B),
                        ('type_range', '=', 'hours'),
                    ], limit=1)

                    self.env['fleet.vehicle.log.services'].create({
                        'service_type_id': services_type.id if services_type else False,
                        'vehicle_id': v.id,
                        'type_service_id': services_config.id if services_config else False,
                    })
                    v.horometro_control_1600 = 0

                if v.horometro_control_4000 >= v.mantenimiento_C:
                    # create service 4000
                    services_config = self.env['fleet.services.config'].search([
                        ('quantity', '=', v.mantenimiento_C),
                        ('type_range', '=', 'hours'),
                    ], limit=1)

                    self.env['fleet.vehicle.log.services'].create({
                        'service_type_id': services_type.id if services_type else False,
                        'vehicle_id': v.id,
                        'type_service_id': services_config.id if services_config else False,
                    })
                    v.horometro_control_4000 = 0

            # elif (400 -dff) <=  v.aviso:
            #     # notificacion servicio proximo :
            #     mail_template = self.env.ref ('cdd_sale_fleet.fleet_maintenance_notification',self.id)
            #     mail_template.send_mail(self.id, force_send = True)
        pass