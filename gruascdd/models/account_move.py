from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    pozo = fields.Char("Nombre Pozo")

