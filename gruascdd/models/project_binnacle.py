from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ProjectBinnacle(models.Model):
    _name = "project.binnacle"

    parent_id = fields.Many2one(
        "project.task",
        string="Proyecto",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
        auto_join=True,
    )

    parent_id_int = fields.Integer(' ')

    product_id = fields.Many2one(
        "product.product",
        string="Servicio",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
        domain=[("in_sale_order", "=", parent_id_int)])

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string='Grua'
    )

    date_init = fields.Datetime("Fecha hora inicio")
    date_end = fields.Datetime("Fecha hora final")
    delta = fields.Float("Delta", compute="_compute_delta", store=True)
    folio = fields.Char("Folio")
    pre_parent_id = fields.Many2one("project.task", string="pre_parent")
    odometer_init = fields.Integer("Odómetro inicial")
    odometer_end = fields.Integer("Odómetro final")
    delta_odometer = fields.Integer("Delta odómetro", compute="_compute_delta_odometer", store=True)
    hourmeter_init = fields.Integer("Horómetro inicial")
    hourmeter_end = fields.Integer("Horómetro final")
    delta_hourmeter = fields.Integer("Delta horómetro", compute="_compute_delta_hourmeter", store=True)
    comment = fields.Char("Comentario")

    gruero_id = fields.Many2one(
        "hr.employee",
        "Gruero"
    )

    ayudante_id = fields.Many2one(
        "hr.employee",
        "Ayudante"
    )

    available_product_ids = fields.Many2many(
        "product.product",
        compute = "_compute_available_product_ids"
    )
    
    @api.depends("available_product_ids", "product_id")
    def _compute_available_product_ids(self):
        for rec in self:
            order_id = rec.env["sale.order"].browse(rec._context.get("active_id"))
            if not order_id:
                task = rec.env["project.task"].browse(rec._context.get("default_parent_id_int"))
                order_id = rec.env["sale.order"].search([("tasks_ids", "in", task.id)], limit=1)
            res = order_id.order_line.mapped("product_id")
            rec.available_product_ids = res

    @api.depends("date_init", "date_end", "delta")
    def _compute_delta(self):
        for rec in self:
            if rec.date_init and rec.date_end:
                rec.delta = (rec.date_end - rec.date_init).total_seconds() / 3600
            else:
                rec.delta = 0
    @api.depends("odometer_init", "odometer_end", "delta_odometer")
    def _compute_delta_odometer(self):
        for rec in self:
            if rec.odometer_init and rec.odometer_end:
                rec.delta_odometer = rec.odometer_end - rec.odometer_init
            else:
                rec.delta_odometer = 0
    @api.depends("hourmeter_init", "hourmeter_end", "delta_hourmeter")
    def _compute_delta_hourmeter(self):
        for rec in self:
            if rec.hourmeter_init and rec.hourmeter_end:
                rec.delta_hourmeter = rec.hourmeter_end - rec.hourmeter_init
            else:
                rec.delta_hourmeter = 0
    @api.onchange("date_init", "date_end")
    def onchange_dates(self):

        if self.date_init and self.date_end:
            if self.date_init >= self.date_end:
                raise ValidationError("La fecha de inicio no puede ser mayor o igual a la fecha final")
    @api.onchange("odometer_init", "odometer_end")
    def onchange_odometer(self):
        if self.odometer_init and self.odometer_end:
            if self.odometer_init > self.odometer_end:
                raise ValidationError("El odómetro inicial no puede ser mayor al final")
    @api.onchange("hourmeter_init", "hourmeter_end")
    def onchange_hourmeter(self):
        if self.hourmeter_init and self.hourmeter_end:
            if self.hourmeter_init > self.hourmeter_end:
                raise ValidationError("El horómetro inicial no puede ser mayor al final")