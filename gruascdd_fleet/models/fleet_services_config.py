from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fleet_services_config_id = fields.Many2one(comodel_name='fleet.services.config', string='')


class FleetServicesConfig(models.Model):
    _name = 'fleet.services.config'
    _description = 'fleet.services.config'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    quantity = fields.Integer(string='Cantidad')
    type_range = fields.Selection(string='Tipo', selection=[('hours', 'Horas'), ('days', 'Dias')], default='hours')
    #partner_notification_ids = fields.One2many(comodel_name='res.partner', inverse_name='fleet_services_config_id', string='')
    value_to_alert = fields.Integer(string='Tiempo antes de Alerta')
    value_month_to_alert = fields.Integer(string='Tiempo en meses para alerta')
    value_horometer_alert = fields.Integer(string='Valor Horometro')
