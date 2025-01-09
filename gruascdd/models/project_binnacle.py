from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import time
from pytz import timezone
import pytz

_logger = logging.getLogger(__name__)

class ProjectBinnacle(models.Model):
    _name = "project.binnacle"
    _description = "Bitácora"

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
    gasolina = fields.Float("Diésel")
    comment = fields.Char("Comentario")
    origen = fields.Selection([
        ('tablet', 'Tableta'),
        ('odoo', 'Odoo')], string='Origen del registro', default='odoo', required=False)
    salto_secuencia = fields.Boolean('Salto en sucencia?', default=False, store=True, compute="_compute_salto_secuencia")
    hourmeter_id = fields.Integer("ID Horómetro")
    odometer_id = fields.Integer("ID Odometer")
    gas_id = fields.Integer("ID Gas")
    

    gruero_id = fields.Many2one(
        "hr.employee",
        "Gruero"
    )

    ayudante_id = fields.Many2one(
        "hr.employee",
        "Ayudante"
    )

    tercer_ayudante_id = fields.Many2one(
        "hr.employee",
        "Tercer Ayudante"
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
            rec.delta_odometer = rec.odometer_end - rec.odometer_init

    @api.depends("hourmeter_init", "hourmeter_end", "delta_hourmeter")
    def _compute_delta_hourmeter(self):
        for rec in self:
            rec.delta_hourmeter = rec.hourmeter_end - rec.hourmeter_init

    @api.depends("date_init", "date_end")
    def _compute_salto_secuencia(self):

        for i in self:
            bandera = False
            tz = self.env.user.tz # Find Timezone from user or partner or employee
            att_tz = timezone(tz or 'utc') 
            
            binnacle = self.env['project.binnacle'].sudo().search([('parent_id_int', '=', i.parent_id_int)], order='date_init asc')

            if binnacle:
                for line in binnacle[0]:
                    self.env['project.binnacle'].sudo().search([('id', '=', line.id)]).write({"salto_secuencia": False})
                
                for i in binnacle[1:]:
                    attendance_dt = datetime.strptime(str(i.date_init), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
                    att_tz_dt = pytz.utc.localize(attendance_dt)
                    local_date_init = att_tz_dt.astimezone(att_tz)
                    date_before = local_date_init.date() + timedelta(days=-1)
                
                        #_logger.info("date_before:" + str(date_before))
                        #_logger.info("local_date_init:" + str(local_date_init.date()))
                            
                    for j in binnacle:
                        attendance_dt = datetime.strptime(str(j.date_end), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
                        att_tz_dt = pytz.utc.localize(attendance_dt)
                        local_date_end_db = att_tz_dt.astimezone(att_tz) # converted value to tz
                
                            #_logger.info("local_date_end_db:" + str(local_date_end_db.date()))
                
                        if local_date_end_db.date() == date_before or local_date_end_db.date() == local_date_init.date():
                            bandera = False
                            break
                        else:
                            bandera = True
                
                    self.env['project.binnacle'].sudo().search([('id', '=', i.id)]).write({"salto_secuencia": bandera})  
            
                
    @api.onchange("date_init", "date_end")
    def onchange_date(self):

        if self.date_init and self.date_end:
            if self.date_init >= self.date_end:
                raise ValidationError("La fecha de inicio no puede ser mayor o igual a la fecha final")
        
    
    @api.onchange("odometer_init","odometer_end")
    def onchange_odometer_end(self):
        if self.odometer_init and self.odometer_end:
            if self.odometer_init > self.odometer_end:
                raise ValidationError("El odómetro inicial no puede ser mayor al final") 

    @api.onchange("hourmeter_end","hourmeter_init")
    def onchange_hourmeter_init(self):
        if self.hourmeter_init and self.hourmeter_end:
            if self.hourmeter_init > self.hourmeter_end:
                raise ValidationError("El horómetro inicial no puede ser mayor al final")
            
    @api.onchange("gasolina")
    def onchange_gasolina(self):
        if self.gasolina:
            if self.gasolina < 0:
                raise ValidationError("El valor debe ser mayor que 0")

    @api.model_create_multi
    def create(self, vals_list):
        results = []
        for vals in vals_list:
            # Obtener valores de `vals` o usar los valores del modelo
            date_end = vals.get("date_end", self.date_end)
            date_init = vals.get("date_init", self.date_init)
            vehicle_id = vals.get("vehicle_id", self.vehicle_id)
            hourmeter_end = vals.get("hourmeter_end", self.hourmeter_end)
            odometer_end = vals.get("odometer_end", self.odometer_end)
            gasolina = vals.get("gasolina", self.gasolina)
            gruero_id = vals.get("gruero_id", self.gruero_id)
            parent_id_int = vals.get("parent_id_int", self.parent_id_int)
            folio = vals.get("folio", self.folio)
            tz = self.env.user.tz or 'utc'

            # Convertir fecha a zona horaria del usuario
            att_tz = pytz.timezone(tz)
            attendance_dt = datetime.strptime(str(date_end), DEFAULT_SERVER_DATETIME_FORMAT)
            att_tz_dt = pytz.utc.localize(attendance_dt)
            local_date_end = att_tz_dt.astimezone(att_tz)

            # Crear registros de horómetro, odómetro y gasolina
            vals["hourmeter_id"] = self.env["fleet.vehicle.hourmeter"].sudo().create({
                "date": local_date_end.date(),
                "value": hourmeter_end,
                "vehicle_id": vehicle_id,
                #"driver_employee_id": gruero_id,
                "binnacle_id": self.id,
                "folio": folio,
            }).id

            vals["odometer_id"] = self.env["fleet.vehicle.odometer"].sudo().create({
                "date": local_date_end.date(),
                "value": odometer_end,
                "vehicle_id": vehicle_id,
                #"driver_employee_id": gruero_id,
                "binnacle_id": self.id,
                "folio": folio,
            }).id

            vals["gas_id"] = self.env["fleet.vehicle.gas"].sudo().create({
                "date": local_date_end.date(),
                "value": gasolina,
                "vehicle_id": vehicle_id,
                #"driver_employee_id": gruero_id,
                "binnacle_id": self.id,
                "folio": folio,
            }).id

            # Crear el registro principal
            result = super(ProjectBinnacle, self).create(vals)
            results.append(result)

            # Actualizar saltos de secuencia en el historial
            binnacle_records = self.env['project.binnacle'].sudo().search(
                [('parent_id_int', '=', parent_id_int)],
                order='date_init asc'
            )

            for idx, record in enumerate(binnacle_records):
                bandera = False
                if idx > 0:
                    prev_record = binnacle_records[idx - 1]
                    prev_date_end = pytz.utc.localize(datetime.strptime(
                        str(prev_record.date_end), DEFAULT_SERVER_DATETIME_FORMAT
                    )).astimezone(att_tz).date()

                    current_date_init = pytz.utc.localize(datetime.strptime(
                        str(record.date_init), DEFAULT_SERVER_DATETIME_FORMAT
                    )).astimezone(att_tz).date()

                    bandera = prev_date_end != current_date_init - timedelta(days=1)

                record.sudo().write({"salto_secuencia": bandera})

        return results if len(results) > 1 else results[0]
        
    @api.model
    def write(self, vals):
        bandera = False
        tz = self.env.user.tz  # Find Timezone from user or partner or employee
        att_tz = timezone(tz or 'utc') 
        
        date_end = datetime.strptime(vals["date_end"], "%Y-%m-%d %H:%M:%S") if "date_end" in vals else self.date_end
        date_init = datetime.strptime(vals["date_init"], "%Y-%m-%d %H:%M:%S") if "date_init" in vals else self.date_init  
        vehicle_id = vals["vehicle_id"] if "vehicle_id" in vals else self.vehicle_id
        id = vals["id"] if "id" in vals else self.id
        hourmeter_end = vals["hourmeter_end"] if "hourmeter_end" in vals else self.hourmeter_end
        odometer_end = vals["odometer_end"] if "odometer_end" in vals else self.odometer_end
        gasolina = vals["gasolina"] if "gasolina" in vals else self.gasolina
        gruero_id = vals["gruero_id"] if "gruero_id" in vals else self.gruero_id
        parent_id = vals["parent_id"] if "parent_id" in vals else self.parent_id
        folio = vals["folio"] if "folio" in vals else self.folio
        parent_id_int = vals["parent_id_int"] if "parent_id_int" in vals else self.parent_id_int
        hourmeter_id = vals["hourmeter_id"] if "hourmeter_id" in vals else self.hourmeter_id
        odometer_id = vals["odometer_id"] if "odometer_id" in vals else self.odometer_id
        gas_id = vals["gas_id"] if "gas_id" in vals else self.gas_id           
            
        tz = self.env.user.tz  # Find Timezone from user or partner or employee
        att_tz = timezone(tz or 'utc') # If no tz then return in UTC
        attendance_dt = datetime.strptime(str(date_end), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
        att_tz_dt = pytz.utc.localize(attendance_dt)
        local_date_end = att_tz_dt.astimezone(att_tz) # converted value to tz

        result = super(ProjectBinnacle, self).write(vals)
        
        if result:     
            horometer_log = self.env['fleet.vehicle.hourmeter'].sudo().search([('id', '=', hourmeter_id)])
            odometer_log = self.env['fleet.vehicle.odometer'].sudo().search([('id', '=', odometer_id)])
            gas_log = self.env['fleet.vehicle.gas'].sudo().search([('id', '=', gas_id)])
            
            # Actualizar registro del Horómetro en el vehículo
            horometer_log.sudo().write({
                "date": local_date_end.date(),
                "value": hourmeter_end,
                "vehicle_id": vehicle_id.id,
                #"driver_employee_id": gruero_id.id,
                #"driver_id": gruero_id.id,
                "binnacle_id": id,
                "task_name": parent_id.name,
                "folio": folio
            })
        
            # Actualizar registro del Odometro en el vehículo
            odometer_log.sudo().write({
                "date": local_date_end.date(),
                "value": odometer_end,
                "vehicle_id": vehicle_id.id,
                #"driver_employee_id": gruero_id.id,
                #"driver_id": gruero_id.id,
                "binnacle_id": id,
                "task_name": parent_id.name,
                "folio": folio
            })
        
            # Actualizar registro del Diesel en el vehículo
            gas_log.sudo().write({
                "date": local_date_end.date(),
                "value": gasolina,
                "vehicle_id": vehicle_id.id,
                #"driver_employee_id": gruero_id.id,
                #"driver_id": gruero_id.id,
                "binnacle_id": id,
                "task_name": parent_id.name,
                "folio": folio
            })            
     
        return result

    @api.model
    def unlink(self):
        salto_secuencia = False
        parent_id_int = None
        
        for line in self:
            
            tz = self.env.user.tz  # Find Timezone from user or partner or employee
            att_tz = timezone(tz or 'utc') # If no tz then return in UTC
            attendance_dt = datetime.strptime(str(line.date_end), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
            att_tz_dt = pytz.utc.localize(attendance_dt)
            local_date_end = att_tz_dt.astimezone(att_tz) # converted value to tz
    
            horometer_log = self.env['fleet.vehicle.hourmeter'].sudo().search([('id', '=', line.hourmeter_id)])
            odometer_log = self.env['fleet.vehicle.odometer'].sudo().search([('id', '=', line.odometer_id)])
            gas_log = self.env['fleet.vehicle.gas'].sudo().search([('id', '=', line.gas_id)])

            if not parent_id_int:
                parent_id_int = line.parent_id_int
            
            horometer_log.unlink()
            odometer_log.unlink()
            gas_log.unlink()
        
        result = super(ProjectBinnacle, self).unlink()

        #self.env.cr.commit()

        #_logger.info("parent_id_int:" + str(parent_id_int))

        binnacle = self.env['project.binnacle'].sudo().search([('parent_id_int', '=', parent_id_int)], order='date_init asc')

        #_logger.info("len(binnacle):" + str(len(binnacle)))
        
        for line in binnacle[0]:
            self.env['project.binnacle'].sudo().search([('id', '=', line.id)]).write({"salto_secuencia": False})

        for i in binnacle[1:]:
            attendance_dt = datetime.strptime(str(i.date_init), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
            att_tz_dt = pytz.utc.localize(attendance_dt)
            local_date_init = att_tz_dt.astimezone(att_tz)
            date_before = local_date_init.date() + timedelta(days=-1)

            #_logger.info("date_before:" + str(date_before))
            #_logger.info("local_date_init:" + str(local_date_init.date()))
            
            for j in binnacle:
                attendance_dt = datetime.strptime(str(j.date_end), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
                att_tz_dt = pytz.utc.localize(attendance_dt)
                local_date_end_db = att_tz_dt.astimezone(att_tz) # converted value to tz

                #_logger.info("local_date_end_db:" + str(local_date_end_db.date()))

                if local_date_end_db.date() == date_before or local_date_end_db.date() == local_date_init.date():
                    bandera = False
                    break
                else:
                    bandera = True

            self.env['project.binnacle'].sudo().search([('id', '=', i.id)]).write({"salto_secuencia": bandera})
        
        return result
