from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    model_fleet_id = fields.Many2one(
        comodel_name="fleet.vehicle.model",
        string="Modelo de la grúa",
        store=True
    )

    pozo = fields.Char(
        "Pozo"
    )

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['pozo'] = self.pozo

        task = self.env['project.task'].sudo().search([
            ('sale_order_id', '=', self.id)
        ])

        task.write({'stage_id': 177})

        return invoice_vals

    def _get_invoiceable_lines(self, final=False):
        return super(SaleOrder, self)._get_invoiceable_lines(final).filtered(lambda l: not l.product_id.rent_ok)
