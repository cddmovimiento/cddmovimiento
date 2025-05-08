from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import time
from pytz import timezone
import pytz

_logger = logging.getLogger(__name__)

class FleetVehicleBinnacleServices(models.Model):
    _name = "fleet.vehicle.binnacle.services"
    _description = "Bitácora"
    _order = 'date_init DESC'

    parent_id = fields.Many2one(
        "fleet.vehicle.log.services",
        string="Servicio",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
        auto_join=True,
    )
    
    type_activity = fields.Selection(
        string='Actividad', 
        selection=[
            ('transporte_sitio', 'Transporte a Sitio'), 
            ('preparacion', 'Preparación'),
            ('servicio', 'Servicio'),
            ('descanso', 'Descanso'),
            ('fin_servicio','Fin de Servicio'),
            ('transporte_retorno', 'Transporte de Retorno')
        ]
    )

    date_init = fields.Datetime("Fecha hora inicio")
    date_end = fields.Datetime("Fecha hora final")
    delta = fields.Float("Delta", compute="_compute_delta", store=True)


    @api.depends("date_init", "date_end", "delta")
    def _compute_delta(self):
        for rec in self:
            if rec.date_init and rec.date_end:
                rec.delta = (rec.date_end - rec.date_init).total_seconds() / 3600
            else:
                rec.delta = 0