# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    type_employee = fields.Selection(string='Empleado Operativo', selection=[('gruero', 'Gruero'), ('ayudante', 'Ayudante')])

    in_project_task = fields.Integer(
        "in_project_task",
        compute="_compute_in_project_task",
        search="_search_in_project_task"
    )

    @api.depends('name')
    def _compute_in_project_task(self):
        self.in_project_task = 1

    @api.model
    def _search_in_project_task(self, operator, value):
        if operator == "=":
            task = self.env['project.task'].search([("id", "=", value)])
            if task:
                employees = []
                for user in task.employee_ids:
                    if user.id not in employees:
                        employees.append(user.id)
                return [("id", "in", employees)]
            else:
                return False
        else:
            return False

