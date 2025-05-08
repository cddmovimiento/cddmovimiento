from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


# Modelo para los checklist
class FleetServiceCheckList(models.Model):
    _name = 'fleet.service.checklist'
    _description = 'Check list para lista de verificación.'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Nombre',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )

    type_service_id = fields.Many2one(comodel_name='fleet.services.config', string='Tipo de Servicio')


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    _order = 'date DESC'
    _rec_name = 'folio'

    folio = fields.Char(string='Folio', required=True, readonly=True, default=lambda self: _('New'))

    type_service_id = fields.Many2one(comodel_name='fleet.services.config', string='Lista de verificación')
    
    ubicacion = fields.Char(string='Ubicación', required=True)

    hourmeter = fields.Float(string='Último horómetro', help='Horómetro del vehículo en el momento de este registro')
    next_hourmeter = fields.Float(string='Horómetro próximo servicio', help='Horómetro del próximo servicio')

    mecanico = fields.Many2one(
        "hr.employee",
        string="Oficial Mecánico",
        store=True,
        domain=[("type_employee", "=", "mantenimiento")]
    )
    
    electrico = fields.Many2one(
        "hr.employee",
        string="Oficial Eléctrico",
        store=True,
        domain=[("type_employee", "=", "mantenimiento")]
    )
    
    ayudante = fields.Many2one(
        "hr.employee",
        string="Ayudante",
        store=True,
        domain=[("type_employee", "=", "mantenimiento")]
    )

    encargado = fields.Many2one(
        "hr.employee",
        string="Encargado",
        store=True,
        #domain=[("type_employee", "=", "mantenimiento")]
    )

    foliado = fields.Boolean('foliado', default=False)

    tipo_servicio = fields.Selection(
        string='Tipo de Servicio', 
        selection=[
            ('mecanico', 'Mecánico'), 
            ('electrico', 'Eléctrico'),
            ('mecanico_electrico', 'Mecánico-Eléctrico'),
            ('horometro', 'Horómetro')
        ]
    )
    
    binnacle_ids = fields.One2many(
        "fleet.vehicle.binnacle.services",
        "parent_id",
        string="Bitácora"
    )

    verification_list_ids = fields.One2many(
        "fleet.vehicle.verification.list",
        "parent_id",
        string="Lista de verificación"
    )

    failure_ids = fields.One2many(
        "fleet.vehicle.failure.list",
        "parent_id",
        string="Lista de fallas"
    )

    tipo_solicitud = fields.Selection(
        string='Tipo de Solicitud', 
        selection=[
            ('preventivo', 'Preventivo'), 
            ('correctivo', 'Correctivo'),
            ('general', 'Inspección general')
        ]
    )

    folio_relacionado = fields.Many2one(
        "fleet.vehicle.log.services",
        string="Folio referencia",
        store=True
    )
    
    folio_relacionado_domain = fields.Binary(string="folio relacionado domain", compute="onchange_tipo_solicitud")

    folio_rf = fields.Char(string="Folio Reporte falla")
    
    tipo = fields.Char(string="Tipo")

    date_init = fields.Datetime("Fecha hora inicio")
    date_end = fields.Datetime("Fecha hora final")
    delta = fields.Float("Delta")
    descripcion_trabajo = fields.Text(string='Descripcion trabajo', help='Descripción del trabajo')

    @api.model
    def create(self, vals):

        if vals.get('folio', _('New')) == _('New'):

            servicios = self.env['fleet.service.type'].search([('id','=', vals.get('service_type_id', ''))])
            
            for s in servicios:
                if s.name == 'Adicional':
                    vals['folio'] = self.env['ir.sequence'].next_by_code('FleetVehicleLogServices.adicional') or _('New')
                    vals['foliado'] = True
                   
                if s.name == 'Preventivo':
                    vals['folio'] = self.env['ir.sequence'].next_by_code('FleetVehicleLogServices.preventivo') or _('New')
                    vals['foliado'] = True
                   
                if s.name == 'Correctivo':
                    vals['folio'] = self.env['ir.sequence'].next_by_code('FleetVehicleLogServices.correctivo') or _('New')
                    vals['foliado'] = True
  
                if s.name == 'Fallas':
                    vals['folio'] = self.env['ir.sequence'].next_by_code('FleetVehicleLogServices.fallas') or _('New')
                    vals['foliado'] = True

                if s.name not in ('Correctivo', 'Preventivo', 'Adicional', 'Fallas'):
                    vals['folio'] = 'SF'
                    vals['foliado'] = True
                    
                vals['tipo'] = s.name

        res = super(FleetVehicleLogServices, self).create(vals)        
        
        return res

    @api.onchange("type_service_id")
    def onchange_type_service_id(self):
        
        lista_verificacion = []
        

        new_verification_list = self.env['fleet.service.checklist'].sudo().search([('type_service_id', '=', self.type_service_id.id)])
        
        for lv in new_verification_list:
            _logger.info("new_veritication_list:" + lv.name)
            
            lista_verificacion.append((0, 0, {
                'nombre': lv.name
            }))

        for rec in self:
        #rec.verification_list_ids = [(5, 0, 0)] + lista_verificacion
            rec.write({'verification_list_ids': [(5, 0, 0)] + lista_verificacion})

    @api.onchange("tipo_solicitud")
    def onchange_tipo_solicitud(self):
        domain = []
        for r in self:
            if self.tipo_solicitud == 'preventivo':
                domain = [('tipo', '=', 'Preventivo')]
            if self.tipo_solicitud == 'correctivo':
                domain = [('tipo', '=', 'Correctivo')]
            if self.tipo_solicitud not in ('preventivo', 'correctivo'):
                domain = ["!", ("tipo","in",['Correctivo', 'Preventivo'])]

            r.folio_relacionado_domain = domain 
        

