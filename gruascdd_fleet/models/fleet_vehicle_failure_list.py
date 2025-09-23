from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import time
from pytz import timezone
import pytz

_logger = logging.getLogger(__name__)

class FleetVehicleFailureList(models.Model):
    _name = "fleet.vehicle.failure.list"
    _description = "Lista de fallas"

    parent_id = fields.Many2one(
        "fleet.vehicle.log.services",
        string="Servicio",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
        auto_join=True,
    )

    failure = fields.Many2one(
        "fleet.failure.config",
        string="Falla",
        store=True,
        domain=[("active", "=", True)]
    )

    other_text = fields.Char("Especificación")
    description = fields.Char("Descripción")
    
    cantidad = fields.Float(string="Cantidad")

    observaciones = fields.Char(string="Observaciones")

    @api.onchange("failure")
    def onchange_failure(self):
        if not self.failure.especificacion:
            self.other_text = self.failure.name