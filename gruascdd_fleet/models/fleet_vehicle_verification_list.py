from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import time
from pytz import timezone
import pytz

_logger = logging.getLogger(__name__)

class FleetVehicleVerificationList(models.Model):
    _name = "fleet.vehicle.verification.list"
    _description = "Lista de verificación"

    parent_id = fields.Many2one(
        "fleet.vehicle.log.services",
        string="Servicio",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
        auto_join=True,
    )

    nombre = fields.Char(
        string='Nombre'
    )
    
    opcion = fields.Selection(
        string='Opciones', 
        selection=[
            ('si', 'Sí'), 
            ('no', 'No')
        ]
    )

    cantidad = fields.Float(string="Cantidad")

    observaciones = fields.Char(string="Observaciones")