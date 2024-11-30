# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError
#from datetime import datetime

class HorasNomina(models.Model):
    _name = 'horas.nomina'
    _description = 'HorasNomina'

    name = fields.Char("Name", required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    fecha = fields.Date('Fecha')
    tipo_de_hora = fields.Selection([('1','Simple'),
                                      ('2','Doble'),
                                      ('3', 'Triple')], string='Tipo de hora extra')
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Hecho'), ('cancel', 'Cancelado')], string='Estado', default='draft')
    horas = fields.Char("Horas")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('horas.nomina') or _('New')
        
        # Llamar al método original de creación para procesar en lote
        records = super(HorasNomina, self).create(vals_list)
        return records

    def action_validar(self):
        self.write({'state':'done'})
        return

    def action_cancelar(self):
        self.write({'state':'cancel'})

    def action_draft(self):
        self.write({'state':'draft'})

    def unlink(self):
        raise UserError("Los registros no se pueden borrar, solo cancelar.")