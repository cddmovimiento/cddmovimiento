from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    report_name = fields.Char('report name', compute='get_report_name')

    type_filtered = fields.Selection([
        ('date_create', 'Fecha de creacion'),
        ('date_ejec', 'Fecha de ejecucion'),
        ('uni_eco', 'Unidad ecónomica'),
        ('state', 'Etapa'),
        ('all', 'Todos'),
    ], string='Tipo de filtro')

    state_wizard = fields.Selection([
        ('draft', 'Cotizacion'),
        ('sent', 'Cotizacion enviada'),
        ('sale ', 'Orden de venta'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado'),
    ], string='Estatus Cotización')

    vehicle_wizard_id = fields.Many2one('fleet.vehicle', string='Unidad ecónomica')

    date_filtered_wizard_init = fields.Datetime('Desde')
    date_filtered_wizard_end = fields.Datetime('Hasta')

    active_task = fields.Boolean(string='Activo', compute='_has_active_task', search='_search_active_task')

    task_date_last_stage_update = fields.Datetime(compute='_compute_date_last_stage_update',
                                                  search='_search_date_last_stage_update')

    @api.depends('tasks_ids', 'tasks_ids.active')
    def _has_active_task(self):
        if self.tasks_ids:
            self.active_task = tasks_ids[0].active;

    @api.depends('tasks_ids', 'tasks_ids.vehicle_id')
    def _compute_vehicle_id(self):
        if self.tasks_ids:
            self.vehicle_id = self.tasks_ids[0].vehicle_id

    @api.depends('tasks_ids', 'tasks_ids.date_last_stage_update')
    def _compute_date_last_stage_update(self):
        if self.tasks_ids:
            self.task_date_last_stage_update = task.date_last_stage_update

    def _search_date_last_stage_update(self, operator, value):
        orders = self.env['sale.order'].search([('id', '>', 0)])
        ids = [-1]
        for order in orders:
            if order.tasks_ids:
                if operator == '=' and order.tasks_ids[0].date_last_stage_update == value:
                    ids.append(order.id)
                if operator == '<' and order.tasks_ids[0].date_last_stage_update < value:
                    ids.append(order.id)
                if operator == '<=' and order.tasks_ids[0].date_last_stage_update <= value:
                    ids.append(order.id)
                if operator == '>' and order.tasks_ids[0].date_last_stage_update <= value:
                    ids.append(order.id)
                if operator == '<=' and order.tasks_ids[0].date_last_stage_update >= value:
                    ids.append(order.id)
        return [('id', 'in', ids)]

    def _search_active_task(self, operator, value):
        if operator == '=':
            orders = self.env['sale.order'].search([('id', '>', 0)])
            ids = [-1]
            for order in orders:
                if order.tasks_ids:
                    if order.tasks_ids[0].active == value:
                        ids.append(order.id)
            return [('id', 'in', ids)]
        return False

    def _search_vehicle_id(self, operator, value):
        if operator == '=':
            orders = self.env['sale.order'].search([('id', '>', 0)])
            ids = [-1]
            for order in orders:
                if order.tasks_ids:
                    if order.tasks_ids[0].vehicle_id.id == value:
                        ids.append(order.id)
            return [('id', 'in', ids)]
        return False

    def get_report_name(self):
        for rec in self:
            # str (datetime.strptime(str(datetime.now().time()), "%Y-%m-%d"))
            rec.report_name = 'Resumen de actividades' + ' ' + str(datetime.strftime(datetime.now().date(), '%Y%m%d'))

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        if self.tasks_ids:
            total_hours = 0
            for line in self.order_line:
                total_hours += line.product_uom_qty

            self.tasks_ids[0].planned_hours = total_hours
        return result

    def action_report_domain_2(self):
        return {
            'name': 'Reporte diario',
            'type': 'ir.actions.act_window',
            'res_model': 'operations.report.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def get_names_users_assigned(self):
        str_grueros = ''
        if self.tasks_ids:
            grueros_array = self.tasks_ids[0].user_ids.mapped('name')
            for i in grueros_array: str_grueros += (i + ' , ')
        return str_grueros

    def get_date_init(self, line):
        if self.tasks_ids[0] and self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id):
            return self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id).sorted(
                key=lambda r: r.date_init)[0].date_init - timedelta(hours=6)
        else:
            return False

    def get_date_init_2(self, line):
        if self.tasks_ids[0] and self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line):
            return self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line).sorted(
                key=lambda r: r.date_init)[0].date_init - timedelta(hours=6)
        else:
            return False


    def get_date_init_binnacle(self):
        if self.tasks_ids[0] and self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id):
            return self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id).sorted(
                key=lambda r: r.date_init)[0].date_init - timedelta(hours=6)
        else:
            return False


    def get_date_end(self, line):
        if self.tasks_ids[0] and self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id):
            return self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id).sorted(
                key=lambda r: r.date_end)[-1].date_end - timedelta(hours=6)
        else:
            return False

    def get_date_end_2(self, line):
        if self.tasks_ids[0] and self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line):
            return self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line).sorted(
                key=lambda r: r.date_end)[-1].date_end - timedelta(hours=6)
        else:
            return False


    def get_days_total(self, line):
        if self.tasks_ids[0] and self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id):
            init = self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id).sorted(
                key=lambda r: r.date_init)[0].date_init - timedelta(hours=6)
            end = self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id).sorted(
                key=lambda r: r.date_end)[-1].date_end - timedelta(hours=6)
        else:
            return False
        return -1 * (init - end).days

    def get_total_hours(self, line):
        hours = 0
        for rec in self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line.product_id.id):
            hours += rec.delta

        return hours

    def get_total_hours_2(self, line):
        hours = 0

        for rec in self.tasks_ids[0].binnacle_ids.filtered(lambda u: u.product_id.id == line):
            hours += rec.delta

        return hours

    def get_status_invoice_paid(self, status):
        payment_state = 'Sin Facturar'
        if self.invoice_ids:
            if status == 'not_paid':
                payment_state = 'Sin pagar'
            elif status == 'in_payment':
                payment_state = 'En Proceso de Pago'
            elif status == 'paid':
                payment_state = 'Pagado'
            elif status == 'partial':
                payment_state = 'Pagado Parcialmente'
            elif status == 'reversed':
                payment_state = 'Revertido'
            elif status == 'invoicing_legacy':
                payment_state = 'Sistema anterior de facturacion'
        return payment_state

    def get_paid_ammount(self):
        sum = 0
        # _logger.info("Obuener Pago")
        for invoice in self.invoice_ids:
            # _logger.info("invoice Total: %f", invoice.amount_total)
            # _logger.info("invoice : %f", invoice.amount_total)
            sum += abs(invoice.amount_total - invoice.amount_residual)
        return sum
#     @api.onchange('order_line')
#     def recompute_hours_task(self):
#         total_hours = 0
#         for line in self.order_line


#     def _action_confirm(self):
# #         _logger.warning('paso _action_confirm@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
# #         print(errorConfirm)
#         result = super()._action_confirm()
#         if len(self.company_id) == 1:
#             # All orders are in the same company
#             self.order_line.sudo().with_company(self.company_id)._timesheet_service_generation()
#         else:
#             # Orders from different companies are confirmed together

#             for order in self:
#                 order.order_line.sudo().with_company(order.company_id)._timesheet_service_generation()
#         return result


