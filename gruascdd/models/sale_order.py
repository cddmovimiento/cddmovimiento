from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    model_fleet_id = fields.Many2one(
        comodel_name="fleet.vehicle.model",
        string="Modelo de la grúa",
        store=True,
        required=True
    )

    pozo = fields.Char(
        "Pozo",
        required=True
    )


