from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


# Modelo para los checklist
class FleetServiceCheckList(models.Model):
    _name = 'fleet.service.checklist'
    _description = 'Check list para los tipos de servicio.'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Nombre',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    type_service_id = fields.Many2one(comodel_name='fleet.services.config', string='Tipo de Servicio')


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    type_service_id = fields.Many2one(comodel_name='fleet.services.config', string='Tipo de Servicio')

    check_list_ids = fields.Many2many(comodel_name='fleet.service.checklist', string='')

