from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class FleetFailureConfig(models.Model):
    _name = 'fleet.failure.config'
    _description = 'fleet.failure.config'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Nombre falla',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    especificacion = fields.Boolean(String="Solicitar especificación", default=False)

    active = fields.Boolean(String="Activo", default=True)