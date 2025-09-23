from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class FleetServicesType(models.Model):
    _inherit = 'fleet.service.type'

    mobile_enable = fields.Boolean('Disponible en app móvil')
    min_photos = fields.Integer('Número mínimo')