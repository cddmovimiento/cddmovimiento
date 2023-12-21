from odoo import fields, models, api


class ProjectBinnacle(models.Model):
    _name = 'project.binnacle'

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
        domain=[('in_sale_order', '=', parent_id_int)])

    date_init = fields.Datetime('Fecha hora inicio')
    date_end = fields.Datetime('Fecha hora final')
    delta = fields.Float(string='Delta', compute='_compute_delta', store=True)
    pre_parent_id = fields.Many2one('project.task', string='pre_parent')
    odometer = fields.Integer('Odómetro')
    hourmeter = fields.Integer('Horómetro')
    comment = fields.Char('Comentario')

    gruero_id = fields.Many2one(
        "hr.employee",
        string='Gruero'
    )

    ayudante_id = fields.Many2one(
        "hr.employee",
        string='Ayudante'
    )

    available_product_ids = fields.Many2many(
        "product.product",
        compute="_compute_available_product_ids"
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

    @api.depends('date_init', 'date_end', 'delta')
    def _compute_delta(self):
        for rec in self:
            if rec.date_init and rec.date_end:
                rec.delta = (rec.date_end - rec.date_init).total_seconds() / 3600
            else:
                rec.delta = 0