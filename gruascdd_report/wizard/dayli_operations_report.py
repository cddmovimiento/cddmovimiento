import json
from odoo.tools import date_utils
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class AdvancesNotAppliedWizard(models.TransientModel):
    _name = 'dayli.operations.report.wizard'
    _description = 'Wizard para reporte de operaciones'

    start_date = fields.Date(string="Fecha de inicio", required=True)
    end_date = fields.Date(string="Fecha fin", required=True)
    folio = fields.Char("Folio")

    def action_print_report(self):
        vals = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'folio': self.folio
        }
        data = vals

        obj = self.env['project.task'].browse(self._context.get('active_id'))
        #         raise ValidationError('Solo puede eliminar registros en estado inactivo. %s' %(obj))
        obj.sudo().write({
            'start_date_w': self.start_date,
            'end_date_w': self.end_date,
            'folio_w': self.folio
            
        })
        return self.env.ref('gruascdd_report.cdd_action_report_sale_task').report_action(obj)

    @api.constrains('start_date', 'end_date')
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(_('La fecha inicial no puede ser mayor que la final'))


class AdvancesNotAppliedWizard(models.TransientModel):
    _name = 'operations.report.wizard'
    _description = 'Wizard para reporte de operaciones'

    type_filtered = fields.Selection([
        ('date_create', 'Fecha de creacion'),
        ('all', 'Todos'),
    ], string='Tipo de filtro', required=True, default='all')

    state = fields.Selection([
        ('draft', 'Cotizacion'),
        ('sent', 'Cotizacion enviada'),
        ('sale ', 'Orden de venta'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado'),
    ], string='Estatus cotización')

    vehicle_id = fields.Many2one('fleet.vehicle', string='Unidad ecónomica')

    date_filtered_init = fields.Datetime('Desde')
    date_filtered_end = fields.Datetime('Hasta')

    def action_print_report(self):
        #         obj =  self.env['project.task'].browse(self._context.get('active_id'))
        #         raise ValidationError('Solo puede eliminar registros en estado inactivo. %s' %(obj))

        objs = self.env['sale.order'].search([
            ('id', '>', 0)
        ])
        #         raise ValidationError('Solo puede eliminar registros en estado inactivo. %s' %(objs))

        if objs:
            objs.sorted(key=lambda r: r.id)[0].write({
                'type_filtered': self.type_filtered,
                'state_wizard': self.state,
                'vehicle_wizard_id': self.vehicle_id,
                'date_filtered_wizard_init': self.date_filtered_init,
                'date_filtered_wizard_end': self.date_filtered_end,
            })

        objs.env.ref('gruascdd_report.cdd_action_report_sale_task_2').name = objs[0].report_name
        return objs.env.ref('gruascdd_report.cdd_action_report_sale_task_2').report_action(objs)

    def action_print_report_xlsx(self):

        data = {
            'options': json.dumps({
                'type_filtered': self.type_filtered,
                'state': self.state,
                'vehicle_id': self.vehicle_id.id,
                'date_filtered_init': self.date_filtered_init,
                'date_filtered_end': self.date_filtered_end
            }, default=date_utils.json_default)
        }
        objs = self.env['sale.order'].search([
            ('id', '>', 0)
        ])

        if objs:
            objs.sorted(key=lambda r: r.id)[0].write({
                'type_filtered': self.type_filtered,
                'state_wizard': self.state,
                'vehicle_wizard_id': self.vehicle_id,
                'date_filtered_wizard_init': self.date_filtered_init,
                'date_filtered_wizard_end': self.date_filtered_end,
            })

        return self.sudo().env.ref('gruascdd_report.cdd_action_report_sale_task_2_xlsx').report_action(self, data=data)
