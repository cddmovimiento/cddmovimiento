from odoo import fields, models, api


class ModelName(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        planned_hours = self._convert_qty_company_hours(self.company_id)
        sale_line_name_parts = self.name.split('\n')
        description = '<br/>'.join(sale_line_name_parts[1:])
        return {
            "name": "%s : %s" % (self.order_id.name, self.order_id.pozo),
            "allocated_hours": planned_hours,
            "partner_id": self.order_id.partner_id.id,
            "pozo": self.order_id.pozo,
            #"email_from": self.order_id.partner_id.email,
            "description": description,
            "project_id": project.id,
            #'sale_line_id': self.id,
            "sale_order_id": self.order_id.id,
            "company_id": project.company_id.id,
            "user_ids": False,
            "model_fleet_id": self.order_id.model_fleet_id.id,
            'sale_line_id': False,
        }

    def _timesheet_create_task(self, project):
        if self.order_id.tasks_ids:
            return self.order_id.tasks_ids[0]
        else:
            task = self.env['project.task'].sudo().search([('sale_order_id', '=', self.order_id.id)])
            if not task:
                values = self._timesheet_create_task_prepare_values(project)
                task = self.env['project.task'].sudo().create(values)
                self.write({'task_id': task.id})
                task_msg = "This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a>" % (self.order_id.id, self.order_id.name)
                task.message_post(body=task_msg)
                return task
