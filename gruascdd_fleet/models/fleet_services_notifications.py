from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class FleetMaintenanceNotifications(models.Model):
    _name = 'fleet.maintenance.notifications'
    _description = 'fleet.maintenance.notifications'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='email',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    partner_name = fields.Char(string='Usuario')
    send_date = fields.Datetime(string='Fecha de Envio')
    email_id = fields.Many2one(comodel_name='mail.mail', string='Correo Enviado')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string='Vehiculo')

    # email_state	related = email.state
