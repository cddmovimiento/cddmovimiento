# -*- coding: utf-8 -*-

from ast import Bytes
import base64
import json
from unittest import result
from xml.dom import minidom
import requests
import xmltodict
from lxml import etree, objectify
from bs4 import BeautifulSoup
import os
#import time
import datetime
from io import BytesIO
from datetime import timedelta, date
from datetime import time as datetime_time
#from dateutil import relativedelta
from pytz import timezone
from zeep import Client
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from reportlab.graphics.barcode import createBarcodeDrawing #, getCodes
from xml.etree.ElementTree import Element, ElementTree,  SubElement, Comment, parse, tostring, fromstring
from reportlab.lib.units import mm
import math
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import logging
_logger = logging.getLogger(__name__)
import os
import pytz
from odoo import tools
from zeep import Client
from zeep.transports import Transport

from collections import defaultdict, OrderedDict

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    tipo_cpercepcion = fields.Many2one('nomina.percepcion', string='Tipo de percepción')
    tipo_cdeduccion = fields.Many2one('nomina.deduccion', string='Tipo de deducción')
    tipo_cotro_pago = fields.Many2one('nomina.otropago', string='Otros Pagos')

    category_code = fields.Char("Category Code",related="category_id.code",store=True)

    forma_pago = fields.Selection(
        selection=[('001', 'Efectivo'), 
                   ('002', 'Especie'),],
        string=_('Forma de pago'),default='001')
    exencion = fields.Boolean('Percepción con exención de ISR')
    integrar_al_ingreso = fields.Selection(
        selection=[('001', 'Ordinaria'), 
                   ('002', 'Extraordinaria mensual'),
                   ('003', 'Extraordinaria anual'),
                   ('004', 'Parte exenta por día'),],
        string=_('Integrar al ingreso gravable como percepción'))
#    monto_exencion = fields.Float('Exención (UMA)', digits = (12,3))
    variable_imss = fields.Boolean('Percepción variable para el IMSS')
    variable_imss_tipo = fields.Selection(
        selection=[('001', 'Todo el monto'), 
                   ('002', 'Excedente del (% de UMA)'),
                   ('003', 'Excedente del (% de SBC)'),],
        string=_('Tipo'),default='001')
    variable_imss_monto = fields.Float('Monto')
    integrar_ptu = fields.Boolean('Integrar para el PTU')
    integrar_estatal = fields.Boolean('Integrar para el impuesto estatal')
    parte_gravada = fields.Many2one('hr.salary.rule', string='Parte gravada')
    parte_exenta = fields.Many2one('hr.salary.rule', string='Parte exenta')
    cuenta_especie = fields.Many2one('account.account', 'Cuenta de pago', domain=[('deprecated', '=', False)])
    fondo_ahorro_aux = fields.Boolean('Fondo de ahorro')

class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ['hr.payslip','mail.thread']


    tipo_nomina = fields.Selection(
        selection=[('O', 'Nómina ordinaria'), 
                   ('E', 'Nómina extraordinaria'),],
        string=_('Tipo de nómina'), required=True, default='O'
    )

    estado_factura = fields.Selection(
        selection=[('factura_no_generada', 'Factura no generada'), ('factura_correcta', 'Factura correcta'), 
                   ('problemas_factura', 'Problemas con la factura'), ('factura_cancelada', 'Factura cancelada')],
        string=_('Estado de factura'),
        default='factura_no_generada',
        readonly=False
    )	
    imss_dias = fields.Float('Cotizar en el IMSS',default='15') #, readonly=True) 
    imss_mes = fields.Float('Dias a cotizar en el mes',default='30') #, readonly=True)
    xml_nomina_link = fields.Char(string=_('XML link'), readonly=True)
    nomina_cfdi = fields.Boolean('Nomina CFDI')
    qrcode_image = fields.Binary("QRCode")
    qr_value = fields.Char(string=_('QR Code Value'))
    numero_cetificado = fields.Char(string=_('Numero de cetificado'))
    cetificaso_sat = fields.Char(string=_('Cetificao SAT'))
    folio_fiscal = fields.Char(string=_('Folio Fiscal'), copy=False)
    fecha_certificacion = fields.Char(string=_('Fecha y Hora Certificación'))
    cadena_origenal = fields.Char(string=_('Cadena Origenal del Complemento digital de SAT'))
    selo_digital_cdfi = fields.Char(string=_('Selo Digital del CDFI'))
    selo_sat = fields.Char(string=_('Selo del SAT'))
    moneda = fields.Char(string=_('Moneda'))
    tipocambio = fields.Char(string=_('TipoCambio'))
    folio = fields.Char(string=_('Folio'))
    version = fields.Char(string=_('Version'))
    serie_emisor = fields.Char(string=_('Serie'))
    invoice_datetime = fields.Char(string=_('fecha factura'))
    rfc_emisor = fields.Char(string=_('RFC'))
    total_nomina = fields.Float('Total a pagar')
    subtotal = fields.Float('Subtotal')
    descuento = fields.Float('Descuento')
    number_folio = fields.Char(string=_('No. Folio'), compute='_get_number_folio')
    fecha_factura = fields.Datetime(string=_('Fecha Factura'), readonly=True)
    subsidio_periodo = fields.Float('subsidio_periodo')
    isr_periodo = fields.Float('isr_periodo')
    retencion_subsidio_pagado = fields.Float('retencion_subsidio_pagado')
    importe_imss = fields.Float('importe_imss')
    importe_isr = fields.Float('importe_isr')
    periodicidad = fields.Float('periodicidad')
    concepto_periodico = fields.Boolean('Conceptos periodicos', default = True)

    #imss empleado
    emp_exedente_smg = fields.Float(string='Exedente 3 SMGDF.')
    emp_prest_dinero = fields.Float(string='Prest en dinero')
    emp_esp_pens = fields.Float(string='P. Esp. Desp.')
    emp_invalidez_vida = fields.Float( string='Invalidez y Vida.')
    emp_cesantia_vejez = fields.Float(string='Cesantia y vejez.')
    emp_total = fields.Float(string='IMSS trabajador')
    #imss patronal
    pat_cuota_fija_pat = fields.Float(string='Cuota fija patronal')
    pat_exedente_smg = fields.Float(string='Exedente 3 SMGDF')
    pat_prest_dinero = fields.Float(string='Prest. en dinero')
    pat_esp_pens = fields.Float(string='P. Esp. Desp')
    pat_riesgo_trabajo = fields.Float( string='Riegso de trabajo')
    pat_invalidez_vida = fields.Float( string='Invalidez y Vida')
    pat_guarderias = fields.Float(string='Guarderias y PS')
    pat_retiro = fields.Float( string='Retiro')
    pat_cesantia_vejez = fields.Float(string='Cesantia y vejez')
    pat_infonavit = fields.Float(string='INFONAVIT')
    pat_total = fields.Float(string='IMSS patron')

    forma_pago = fields.Selection(
        selection=[('99', '99 - Por definir'),],
        string=_('Forma de pago'),default='99',
    )	
    tipo_comprobante = fields.Selection(
        selection=[('N', 'Nómina'),],
        string=_('Tipo de comprobante'),default='N',
    )	
    tipo_relacion = fields.Selection(
        selection=[('04', 'Sustitución de los CFDI previos'),],
        string=_('Tipo relación'),
    )
    uuid_relacionado = fields.Char(string=_('CFDI Relacionado'))
    methodo_pago = fields.Selection(
        selection=[('PUE', _('Pago en una sola exhibición')),],
        string=_('Método de pago'), default='PUE',
    )	
    uso_cfdi = fields.Selection(
        selection=[
            ('P01', _('Por definir')),
            ('CN01', _('Nomina')),
        ],
        string=_('Uso CFDI (cliente)'),default='CN01',
    )
    fecha_pago = fields.Date(string=_('Fecha de pago'))
    dias_pagar = fields.Float('Pagar en la nomina')
    no_nomina = fields.Selection(
        selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')], string=_('Nómina del mes'))
    acum_per_totales = fields.Float('Percepciones totales', compute='_get_percepciones_totales')
    acum_per_grav  = fields.Float('Percepciones gravadas', compute='_get_percepciones_gravadas')
    acum_isr  = fields.Float('ISR', compute='_get_isr')
    acum_isr_antes_subem  = fields.Float('ISR antes de SUBEM', compute='_get_isr_antes_subem')
    acum_subsidio_aplicado  = fields.Float('Subsidio aplicado', compute='_get_subsidio_aplicado')
    acum_fondo_ahorro = fields.Float('Fondo ahorro', compute='_get_fondo_ahorro')
    dias_periodo = fields.Float(string=_('Dias en el periodo'), compute='_get_dias_periodo')
    isr_devolver = fields.Boolean(string='Devolver ISR')
    isr_ajustar = fields.Boolean(string='Ajustar ISR en cada nómina')
    acum_sueldo = fields.Float('Sueldo', compute='_get_sueldo')

    mes = fields.Selection(
        selection=[('01', 'Enero'), 
                   ('02', 'Febrero'), 
                   ('03', 'Marzo'),
                   ('04', 'Abril'), 
                   ('05', 'Mayo'),
                   ('06', 'Junio'),
                   ('07', 'Julio'),
                   ('08', 'Agosto'),
                   ('09', 'Septiembre'),
                   ('10', 'Octubre'),
                   ('11', 'Noviembre'),
                   ('12', 'Diciembre'),
                   ],
        string=_('Mes de la nómina'))
    nom_liquidacion = fields.Boolean(string='Nomina de liquidacion', default=False)

    #Cancel cfdi 4.0 fields
    type_cancel = fields.Selection([
            ('01', '01|Comprobante emitido con errores con relación.'),
            ('02', '02|Comprobante emitido con errores sin relación.'),
            ('03', '03|No se llevó a cabo la operación.'),
            ('04', '04|Operación nominativa relacionada en una factura global.'),
        ], 
        string= 'Tipo cancelacion', 
        default=False, 
        help='En el caso de que el motivo de cancelación sea "01 - Comprobante emitido con errores con relación" se deberá especificar el UUID del comprobante que sustituye al comprobante a cancelar.')
    uuid_replace_cancel = fields.Char("UUID a sustituir")

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = [(5,0,0)]
        tipo_de_hora_mapping = {'1':'HEX1', '2':'HEX2', '3':'HEX3'}
        horas_obj = self.env['horas.nomina']
        def is_number(s):
            try:
                return float(s)
            except ValueError:
                return 0

        # fill only if the contract as a working schedule linked
        resource_days = []
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.datetime.combine(fields.Date.from_string(date_from), datetime_time.min)
            day_to = datetime.datetime.combine(fields.Date.from_string(date_to), datetime_time.max)
            #day_from = date_from
            #day_to = date_to
            nb_of_days = (day_to - day_from).days + 1

            # compute Prima vacacional
            if contract.tipo_prima_vacacional == '01':
                date_start = contract.date_start
                if date_start:
                    d_from = fields.Date.from_string(date_from)
                    d_to = fields.Date.from_string(date_to)
                
                    date_start = fields.Date.from_string(date_start)
                    if datetime.datetime.today().year > date_start.year:
                        d_from = d_from.replace(date_start.year)
                        if str(d_to.day) == '29' and str(d_to.month) == '2':
                            d_to -=  datetime.timedelta(days=1)
                        d_to = d_to.replace(date_start.year)
                        
                        if d_from <= date_start <= d_to:
                            diff_date = date_to - contract.date_start
                            years = diff_date.days /365.0
                            antiguedad_anos = int(years)
                            tabla_antiguedades = contract.tablas_cfdi_id.tabla_antiguedades.filtered(lambda x: x.antiguedad <= antiguedad_anos)
                            tabla_antiguedades = tabla_antiguedades.sorted(lambda x:x.antiguedad, reverse=True)
                            vacaciones = tabla_antiguedades and tabla_antiguedades[0].vacaciones or 0
                            prima_vac = tabla_antiguedades and tabla_antiguedades[0].prima_vac or 0
                            pvc_type = self.env['hr.work.entry.type'].search([('code','=','PVC')])
                            attendances = (0,0,{                                 
                                 'work_entry_type_id': pvc_type.id,
                                 'name': 'PVC',
                                 'number_of_days': vacaciones * prima_vac / 100.0, #work_data['days'],
                                 #'number_of_hours': 1['hours'],
                            })
                            res.append(attendances)

            # compute Prima dominical
            if contract.prima_dominical:
                domingos = 0
                d_from = fields.Date.from_string(date_from)
                d_to = fields.Date.from_string(date_to)
                for i in range((d_to - d_from).days + 1):
                    if (d_from + datetime.timedelta(days=i+1)).weekday() == 0:
                        domingos = domingos + 1
                pdm_type = self.env['hr.work.entry.type'].search([('code','=','PDM')])
                attendances = (0,0,{
                            'work_entry_type_id': pdm_type.id,
                            'name': 'PDM',
                            'number_of_days': domingos, #work_data['days'],
                            #'number_of_hours': 1['hours'],
                     })
                res.append(attendances)

            # compute leave days
            leaves = {}
            leave_days = 0
            factor = 0
            if contract.semana_inglesa:
                factor = 7.0/5.0
            else:
                factor = 7.0/6.0

            if contract.periodicidad_pago == '04':
                dias_pagar = 15
            if contract.periodicidad_pago == '02':
                dias_pagar = 7

            leaves = leaves = self.env['hr.leave'].search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', 'not in', ['refuse','draft']),
            ])
            for holiday in leaves:
                if not holiday.holiday_status_id.work_entry_type_id:
                    raise ValidationError("Necesitas agregar un tipo de tiempo de trabajo para el tipo de ausencia:\n"
                                          + holiday.holiday_status_id.name)
    
                work_hours = holiday.number_of_hours_display
                #current_leave_struct['number_of_hours'] += leave_time
                if contract.septimo_dia:
                    if contract.incapa_sept_dia:
                        if holiday.holiday_status_id.name == 'FJS' or holiday.holiday_status_id.name == 'FI' or holiday.holiday_status_id.name == 'FR' or holiday.holiday_status_id.name == 'INC_EG' or holiday.holiday_status_id.name == 'INC_RT' or holiday.holiday_status_id.name == 'INC_MAT':
                            leave_days += (holiday.number_of_days)*factor
                            if leave_days > dias_pagar:
                                leave_days = dias_pagar
                        else:
                            if holiday.holiday_status_id.name != 'DFES' and holiday.holiday_status_id.name != 'DFES_3':
                                leave_days += holiday.number_of_days
                    else:
                        if holiday.holiday_status_id.name == 'FJS' or holiday.holiday_status_id.name == 'FI' or holiday.holiday_status_id.name == 'FR':
                            leave_days += (holiday.number_of_days)*factor
                            if leave_days > dias_pagar:
                                leave_days = dias_pagar
                        else:
                            if holiday.holiday_status_id.name != 'DFES' and holiday.holiday_status_id.name != 'DFES_3':
                                leave_days += holiday.number_of_days
                elif work_hours:
                    if contract.incapa_sept_dia:
                        if holiday.holiday_status_id.name == 'INC_EG' or holiday.holiday_status_id.name == 'INC_RT' or holiday.holiday_status_id.name == 'INC_MAT':
                            leave_days += (holiday.number_of_days)*factor
                        else:
                            if holiday.holiday_status_id.name != 'DFES' and holiday.holiday_status_id.name != 'DFES_3':
                                leave_days += holiday.number_of_days
                    else:
                        if holiday.holiday_status_id.name != 'DFES' and holiday.holiday_status_id.name != 'DFES_3':
                            leave_days += holiday.number_of_days
                if leave_days > 0:
                    current_leave_struct = (0,0,{
                        'work_entry_type_id': holiday.holiday_status_id.work_entry_type_id.id,
                        'name': holiday.holiday_status_id.name or 'GLOBAL',
                        'number_of_days': leave_days,
                        'number_of_hours': work_hours,
                    })
                    res.append(current_leave_struct)


            # compute worked days
            #work_data = contract.employee_id.with_context(no_tz_convert=True)._get_work_days_data_batch(day_from, day_to, calendar=contract.resource_calendar_id)
            work_data = contract.employee_id.with_context(no_tz_convert=True)._get_work_days_data_batch(day_from, day_to, calendar=contract.resource_calendar_id)
            resource_days = nb_of_days
            number_of_days = 0

            # ajuste en caso de nuevo ingreso
            nvo_ingreso = False
            date_start_1 = contract.date_start
            date_start_1 = date_start_1
            d_from_1 = date_from
            d_to_1 = date_to
            if date_start_1 > d_from_1:
                   work_data['days'] =  (d_to_1 - date_start_1).days + 1
                   nvo_ingreso = True

            #dias_a_pagar = contract.dias_pagar
            #_logger.info('dias trabajados %s  dias incidencia %s', work_data['days'], leave_days)

            if resource_days < 100:
                #periodo para nómina quincenal
               if contract.periodicidad_pago == '04':
                   if contract.tipo_pago == '01' and nb_of_days < 30:
                      total_days = resource_days + leave_days
                      if total_days != 15:
                         if leave_days == 0 and not nvo_ingreso:
                            number_of_days = 15
                         elif nvo_ingreso:
                            number_of_days = resource_days - leave_days
                         else:
                            number_of_days = 15 - leave_days
                      else:
                         number_of_days = resource_days
                      if contract.sept_dia:
                         aux = 2.5
                         number_of_days -=  aux
                         attendances = (0,0,{
                             'work_entry_type_id': 1,
                             'name': "SEPT",
                             'number_of_days': aux, 
                             'number_of_hours': 0.0,
                         })
                         res.append(attendances)
                   elif contract.tipo_pago == '03' and nb_of_days < 30:
                      total_days = resource_days + leave_days
                      if total_days != 15.21:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = 15.21
                         elif nvo_ingreso:
                            number_of_days = resource_days * 15.21 / 15 - leave_days
                         else:
                            number_of_days = 15.21 - leave_days
                      else:
                         number_of_days = resource_days * 15.21 / 15
                      if contract.sept_dia:
                         aux = 2.21
                         number_of_days -=  aux
                         attendances = (0,0,{
                             'work_entry_type_id': 1,
                             'name': "SEPT",
                             'number_of_days': aux, 
                             'number_of_hours': 0.0,
                         })
                         res.append(attendances)
                   else:
                      delta = date_to - date_from
                      dias_periodo = delta.days + 1
                      total_days = resource_days + leave_days
                      if total_days != dias_periodo:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = dias_periodo
                         elif nvo_ingreso:
                            number_of_days = resource_days - leave_days
                         else:
                            number_of_days = dias_periodo - leave_days
                      else:
                         number_of_days = resource_days
               #calculo para nóminas semanales
               elif contract.periodicidad_pago == '02' and nb_of_days < 30:
                   number_of_days = resource_days
                   if contract.septimo_dia: #falta proporcional por septimo día
                      total_days = resource_days + leave_days
                      if total_days != 7:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = 7
                         elif nvo_ingreso:
                            number_of_days = resource_days - leave_days
                         else:
                            number_of_days = 7 - leave_days
                      else:
                         number_of_days = resource_days
                   if contract.sept_dia: # septimo día
                      if number_of_days == 0:
                         if leave_days != 7:
                            number_of_days = resource_days
                      if contract.semana_inglesa:
                         aux = number_of_days / 7 * 2
                      else:
                         aux = number_of_days - int(number_of_days)
                      _logger.info('number_of_days %s  aux %s', number_of_days, aux)
                      if aux > 0:
                         number_of_days -=  aux
                      elif number_of_days > 0:
                         if contract.semana_inglesa:
                            aux = 2
                         else:
                            aux = 1
                         number_of_days -=  aux
                      attendances = (0,0,{
                          'work_entry_type_id': 1,
                          'name': "SEPT",
                          'number_of_days': aux, 
                          'number_of_hours': 0.0,
                      })
                      res.append(attendances)
               #calculo para nóminas mensuales
               elif contract.periodicidad_pago == '05':
                  if contract.tipo_pago == '01':
                      total_days = resource_days + leave_days
                      if total_days != 30:
                         if leave_days == 0 and not nvo_ingreso:
                            number_of_days = 30
                         elif nvo_ingreso:
                            number_of_days = resource_days - leave_days
                         else:
                            number_of_days = 30 - leave_days
                      else:
                         number_of_days = resource_days
                  elif contract.tipo_pago == '03':
                      total_days = resource_days + leave_days
                      if total_days != 30.42:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = 30.42
                         elif nvo_ingreso:
                            number_of_days = resource_days * 30.42 / 30 - leave_days
                         else:
                            number_of_days = 30.42 - leave_days
                      else:
                         number_of_days =resource_days * 30.42 / 30
                  else:
                      dias_periodo = date_to - date_from.days + 1
                      total_days = resource_days + leave_days
                      if total_days != dias_periodo:
                         if leave_days == 0  and not nvo_ingreso:
                            number_of_days = dias_periodo
                         elif nvo_ingreso:
                            number_of_days = resource_days - leave_days
                         else:
                            number_of_days = dias_periodo - leave_days
                      else:
                         number_of_days = resource_days
               else:
                  number_of_days = resource_days
            else:
               date_start = contract.date_start
               date_start = date_start
               d_from = date_from
               d_to = date_to
               if date_start > d_from:
                   number_of_days =  (d_to - date_start).days + 1 - leave_days
               else:
                   number_of_days =  (d_to - d_from).days + 1 - leave_days
            attendances = (0,0,{
                'work_entry_type_id': 1,
                'name': 'WORK100',
                'number_of_days': number_of_days, #work_data['days'],
                'number_of_hours': round(number_of_days*8,2), # work_data['hours'],
            })

            res.append(attendances)

            #Compute horas extas
            horas = horas_obj.search([('employee_id','=',contract.employee_id.id),('fecha','>=',date_from), ('fecha', '<=', date_to),('state','=','done')])
            horas_by_tipo_de_horaextra = defaultdict(list)
            for h in horas:
                horas_by_tipo_de_horaextra[h.tipo_de_hora].append(h.horas)
            
            for tipo_de_hora, horas_set in horas_by_tipo_de_horaextra.items():
                work_code = tipo_de_hora_mapping.get(tipo_de_hora,'')
                number_of_days = len(horas_set)
                number_of_hours = sum(is_number(hs) for hs in horas_set)
                     
                attendances = (0,0,{
                    'work_entry_type_id': 1,
                    'name': work_code,
                    'number_of_days': number_of_days, 
                    'number_of_hours': number_of_hours,
                })
                res.append(attendances)
                
            #res.extend(leaves.values())
        
        return res

    def set_fecha_pago(self, payroll_name):
            values = {
                'payslip_run_id': payroll_name
                }
            self.update(values)

    @api.onchange('date_to')
    def _get_fecha_pago(self):
        if self.date_to:
            values = {
                'fecha_pago': self.date_to
                }
            self.update(values)

    @api.onchange('date_to')
    def _get_dias_periodo(self):
        self.dias_periodo = 0
        if self.date_to and self.date_from and self.contract_id.periodicidad_pago == '02':
            line = self.contract_id.env['tablas.periodo.semanal'].search([('form_id','=',self.contract_id.tablas_cfdi_id.id),('dia_fin','>=',self.date_to),
                                                                    ('dia_inicio','<=',self.date_to)],limit=1)
            if line:
                _logger.info('encontró periodo..%s', line.no_periodo)
                self.dias_periodo = line.no_dias
            else:
                raise UserError(_('No están configurados correctamente los periodos semanales en las tablas CFDI'))

    @api.model
    def create(self, vals):
        if not vals.get('fecha_pago') and vals.get('date_to'):
            vals.update({'fecha_pago': vals.get('date_to')})
            
        res = super(HrPayslip, self).create(vals)
        return res
    
    @api.depends('number')
    def _get_number_folio(self):
        if self.number:
            self.number_folio = self.number.replace('SLIP','').replace('/','')
        else:
            self.write({'number': self.env['ir.sequence'].next_by_code('numero.nomina')})
            self.number_folio = self.number.replace('NOM','').replace('/','')

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if self.estado_factura == 'factura_correcta' or self.estado_factura == 'factura_cancelada':
            default['estado_factura'] = 'factura_no_generada'
            default['folio_fiscal'] = ''
            default['fecha_factura'] = None
            default['nomina_cfdi'] = False
        return super(HrPayslip, self).copy(default=default)

    @api.onchange('mes')
    def _get_percepciones_gravadas(self):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                #raise UserError(mes_actual)
                date_start = mes_actual.dia_inicio # r.date_from
                date_end = mes_actual.dia_fin #r.date_to
                domain=[('state','in',['done','paid'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', 'TPERG')])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)

                for employee, payslips in employees.items():
                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total
        self.acum_per_grav = total

    @api.onchange('mes')
    def _get_isr(self):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                date_start = mes_actual.dia_inicio # r.date_from
                date_end = mes_actual.dia_fin #r.date_to
                domain=[('state','in',['done','paid'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', 'ISR2'),('category_id.code','=','DED')])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)

                for employee, payslips in employees.items():
                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total
        self.acum_isr = total

    @api.onchange('mes')
    def _get_isr_antes_subem(self):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                date_start = mes_actual.dia_inicio # r.date_from
                date_end = mes_actual.dia_fin #r.date_to
                domain=[('state','in',['done','paid'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', 'ISR')])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)

                for employee, payslips in employees.items():
                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total
        self.acum_isr_antes_subem = total

    @api.onchange('mes')
    def _get_subsidio_aplicado(self):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                date_start = mes_actual.dia_inicio # r.date_from
                date_end = mes_actual.dia_fin #r.date_to
                domain=[('state','in',['done','paid'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', 'SUB')])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)

                for employee, payslips in employees.items():
                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total
        self.acum_subsidio_aplicado = total

    @api.onchange('mes')
    def _get_fondo_ahorro(self):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                date_start = mes_actual.dia_inicio # r.date_from
                date_end = mes_actual.dia_fin #r.date_to
                domain=[('state','in',['done','paid'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', 'D067'),('category_id.code','=','DED')])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)

                for employee, payslips in employees.items():
                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total
        self.acum_fondo_ahorro = total

    @api.depends('mes')
    def _get_percepciones_totales(self):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                date_start = mes_actual.dia_inicio
                date_end = mes_actual.dia_fin
                domain=[('state','in', ['draft','verify'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', 'TPER')])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)
                for employee, payslips in employees.items():
                    #raise UserError(payslips.items())

                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total

        self.acum_per_totales = total

    @api.depends('mes')
    def _get_sueldo(self):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                date_start = mes_actual.dia_inicio # r.date_from
                date_end = mes_actual.dia_fin #r.date_to
                domain=[('state','in', ['draft','verify'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', 'P001')])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)

                for employee, payslips in employees.items():
                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total
        self.acum_sueldo = total

    def get_acumulado(self, codigo):
        total = 0
        for r in self:
            if r.employee_id and r.mes and r.contract_id.tablas_cfdi_id:
                mes_actual = r.contract_id.tablas_cfdi_id.tabla_mensual.search([('dia_inicio', '<=', r.date_from),('dia_fin', '>=', r.date_to)],limit =1)
                date_start = mes_actual.dia_inicio # r.date_from
                date_end = mes_actual.dia_fin #r.date_to
                domain=[('state','in', ['draft','verify'])]
                if date_start:
                    domain.append(('date_from','>=',date_start))
                if date_end:
                    domain.append(('date_to','<=',date_end))
                domain.append(('employee_id','=',r.employee_id.id))
                rules = self.env['hr.salary.rule'].search([('code', '=', codigo)])
                payslips = self.env['hr.payslip'].search(domain)
                payslip_lines = payslips.mapped('line_ids').filtered(lambda x: x.salary_rule_id.id in rules.ids)
                employees = {}
                for line in payslip_lines:
                    if line.slip_id.employee_id not in employees:
                        employees[line.slip_id.employee_id] = {line.slip_id: []}
                    if line.slip_id not in employees[line.slip_id.employee_id]:
                        employees[line.slip_id.employee_id].update({line.slip_id: []})
                    employees[line.slip_id.employee_id][line.slip_id].append(line)

                for employee, payslips in employees.items():
                    for payslip,lines in payslips.items():
                        for line in lines:
                            total += line.total
            return total

    def build_xml(self):
        payslip_total_TOP = 0
        payslip_total_TDED = 0
        payslip_total_PERG = 0
        payslip_total_PERE = 0
        payslip_total_SEIN = 0
        payslip_total_JPRE = 0

        if self.contract_id.date_end:
            antiguedad = ((self.contract_id.date_end - self.contract_id.date_start) + 1) / 7
        else:
            antiguedad = ((self.date_to - self.contract_id.date_start).days + 1) /7

        print("antiguedad")
        print(antiguedad)
        antiguedad = math.floor(antiguedad)

        #**********  Percepciones ************
        #total_percepciones_lines = self.env['hr.payslip.line'].search(['|',('category_id.code','=','ALW'),('category_id.code','=','BASIC'),('category_id.code','=','ALW3'),('slip_id','=',self.id)])
        percepciones_grabadas_lines = self.env['hr.payslip.line'].search([('category_id.code','in',['ALW','BASIC']),('slip_id','=',self.id),('total','>',0)])
        #  percepciones_grabadas_lines = self.env['hr.payslip.line'].search([('slip_id','=',self.id)])
        lineas_de_percepcion = []
        lineas_de_percepcion_exentas = []
        percepciones_excentas_lines = 0
        _logger.info('Total conceptos %s id %s', len(percepciones_grabadas_lines), self.id)
        if percepciones_grabadas_lines:
            for line in percepciones_grabadas_lines:
                parte_exenta = 0
                parte_gravada = 0
                _logger.info('codigo %s monto %s', line.salary_rule_id.code, line.total)

                if line.salary_rule_id.exencion:
                    percepciones_excentas_lines += 1
                    _logger.info('codigo %s', line.salary_rule_id.parte_gravada.code)
                    concepto_gravado = self.env['hr.payslip.line'].search([('code','=',line.salary_rule_id.parte_gravada.code),('slip_id','=',self.id),('total','>',0)], limit=1)
                    if concepto_gravado:
                        parte_gravada = concepto_gravado.total
                        _logger.info('total gravado %s', concepto_gravado.total)
                    
                    _logger.info('codigo %s', line.salary_rule_id.parte_exenta.code)
                    concepto_exento = self.env['hr.payslip.line'].search([('code','=',line.salary_rule_id.parte_exenta.code),('slip_id','=',self.id),('total','>',0)], limit=1)
                    if concepto_exento:
                        parte_exenta = concepto_exento.total
                        _logger.info('total gravado %s', concepto_exento.total)
                    
                    # horas extras
                    if line.salary_rule_id.tipo_cpercepcion.clave == '019':
                        percepciones_horas_extras = self.env['hr.payslip.worked_days'].search([('payslip_id','=',self.id)])
                        if percepciones_horas_extras:
                            _logger.info('si hay ..')
                            for ext_line in percepciones_horas_extras:
                                #_logger.info('codigo %s.....%s ', line.code, ext_line.code)
                                if line.code == ext_line.code:
                                    if line.code == 'HEX1':
                                        tipo_hr = '03'
                                    elif line.code == 'HEX2':
                                        tipo_hr = '01'
                                    elif line.code == 'HEX3':
                                        tipo_hr = '02'
                                    lineas_de_percepcion_exentas.append({'TipoPercepcion': line.salary_rule_id.tipo_cpercepcion.clave,
                                       'Clave': line.code,
                                       'Concepto': line.salary_rule_id.name,
                                       'ImporteGravado': parte_gravada,
                                       'ImporteExento': parte_exenta,
                                       'Dias': ext_line.number_of_days,
                                       'TipoHoras': tipo_hr,
                                       'HorasExtra': ext_line.number_of_hours,
                                       'ImportePagado': line.total})
                    
                    # Ingresos en acciones o títulos valor que representan bienes
                    elif line.salary_rule_id.tipo_cpercepcion.clave == '045':
                        lineas_de_percepcion_exentas.append({
                            'TipoPercepcion': line.salary_rule_id.tipo_cpercepcion.clave,
                            'Clave': line.code,
                            'Concepto': line.salary_rule_id.name,
                            'ValorMercado': 56,
                            'PrecioAlOtorgarse': 48,
                            'ImporteGravado': parte_gravada,
                            'ImporteExento': parte_exenta})
                    else:
                        lineas_de_percepcion_exentas.append({
                            'TipoPercepcion': line.salary_rule_id.tipo_cpercepcion.clave,
                            'Clave': line.code,
                            'Concepto': line.salary_rule_id.name,
                            'ImporteGravado': round(parte_gravada,2),
                            'ImporteExento': round(parte_exenta,2)})
                else:
                    parte_gravada = line.total
                    lineas_de_percepcion.append({
                    'TipoPercepcion': line.salary_rule_id.tipo_cpercepcion.clave,
                    'Clave': line.code,
                    'Concepto': line.salary_rule_id.name,
                    'ImporteGravado': round(line.total,2),
                    'ImporteExento': '0'})

                #if line.salary_rule_id.tipo_cpercepcion.clave != '022' and line.salary_rule_id.tipo_cpercepcion.clave != '023' and line.salary_rule_id.tipo_cpercepcion.clave != '025' and line.salary_rule_id.tipo_cpercepcion.clave !='039' and line.salary_rule_id.tipo_cpercepcion.clave !='044':
                payslip_total_PERE += round(parte_exenta,2)
                payslip_total_PERG += round(parte_gravada,2)
                if line.salary_rule_id.tipo_cpercepcion.clave == '022' or line.salary_rule_id.tipo_cpercepcion.clave == '023' or line.salary_rule_id.tipo_cpercepcion.clave == '025':
                    payslip_total_SEIN += round(line.total,2)
                if line.salary_rule_id.tipo_cpercepcion.clave =='039' or line.salary_rule_id.tipo_cpercepcion.clave =='044':
                    payslip_total_JPRE += round(line.total,2)

        percepcion = {
               'Totalpercepcion': {
                        'TotalSeparacionIndemnizacion': payslip_total_SEIN,
                        'TotalJubilacionPensionRetiro': payslip_total_JPRE,
                        'TotalGravado': round(payslip_total_PERG,2),
                        'TotalExento': round(payslip_total_PERE,2),
                        'TotalSueldos': round(payslip_total_PERG + payslip_total_PERE - payslip_total_SEIN - payslip_total_JPRE,2),
               },
        }

        #************ SEPARACION / INDEMNIZACION   ************#
        if payslip_total_SEIN > 0:
            if payslip_total_PERG > self.contract_id.wage:
                ingreso_acumulable = self.contract_id.wage
            else:
                ingreso_acumulable = payslip_total_PERG
            if payslip_total_PERG - self.contract_id.wage < 0:
                ingreso_no_acumulable = 0
            else:
                ingreso_no_acumulable = payslip_total_PERG - self.contract_id.wage

            percepcion.update({
               'separacion': [{
                        'TotalPagado': payslip_total_SEIN,
                        'NumAñosServicio': self.contract_id.antiguedad_anos,
                        'UltimoSueldoMensOrd': self.contract_id.wage,
                        'IngresoAcumulable': ingreso_acumulable,
                        'IngresoNoAcumulable': ingreso_no_acumulable,
                }]
            })

        #percepcion.update({'SeparacionIndemnizacion': separacion})
        percepcion.update({'lineas_de_percepcion_grabadas': lineas_de_percepcion, 'no_per_grabadas': len(percepciones_grabadas_lines)-percepciones_excentas_lines})
        percepcion.update({'lineas_de_percepcion_excentas': lineas_de_percepcion_exentas, 'no_per_excentas': percepciones_excentas_lines})
        request_params = {'percepciones': percepcion}

        #****** OTROS PAGOS ******
        otrospagos_lines = self.env['hr.payslip.line'].search([('category_id.code','=','ALW3'),('slip_id','=',self.id),('total','>',0)])
        #tipo_otro_pago_dict = dict(self.env['hr.salary.rule']._fields.get('tipo_otro_pago').selection)
        auxiliar_lines = self.env['hr.payslip.line'].search([('category_id.code','=','AUX'),('slip_id','=',self.id),('total','>',0)])
        #tipo_otro_pago_dict = dict(self.env['hr.salary.rule']._fields.get('tipo_otro_pago').selection)
        lineas_de_otros = []
        if otrospagos_lines:
            for line in otrospagos_lines:
                #_#logger.info('line total ...%s', line.total)
                if line.salary_rule_id.tipo_cotro_pago.clave == '002': # and line.total > 0:
                    #line2 = self.contract_id.env['tablas.subsidio.line'].search([('form_id','=',self.contract_id.tablas_cfdi_id.id),('lim_inf','<=',self.contract_id.wage)],order='lim_inf desc',limit=1)
                    self.subsidio_periodo = 0
                    #_logger.info('entro a este ..')
                    payslip_total_TOP += line.total
                    #if line2:
                    #    self.subsidio_periodo = (line2.s_mensual/self.imss_mes)*self.imss_dias
                    for aux in auxiliar_lines:
                        if aux.code == 'SUB':
                            self.subsidio_periodo = aux.total
                    _logger.info('subsidio aplicado %s importe excento %s', self.subsidio_periodo, line.total)
                    lineas_de_otros.append({'TipoOtrosPagos': line.salary_rule_id.tipo_cotro_pago.clave,
                    'Clave': line.code,
                    'Concepto': line.salary_rule_id.name,
                    'ImporteGravado': '0',
                    'ImporteExento': round(line.total,2),
                    'SubsidioCausado': self.subsidio_periodo})
                else:
                    payslip_total_TOP += line.total
                    #_logger.info('entro al otro ..')
                    lineas_de_otros.append({'TipoOtrosPagos': line.salary_rule_id.tipo_cotro_pago.clave,
                        'Clave': line.code,
                        'Concepto': line.salary_rule_id.name,
                        'ImporteGravado': '0',
                        'ImporteExento': round(line.total,2)})
        otrospagos = {
            'otrospagos': {
                    'Totalotrospagos': payslip_total_TOP,
            },
        }
        otrospagos.update({'otros_pagos': lineas_de_otros, 'no_otros_pagos': len(otrospagos_lines)})
        request_params.update({'otros_pagos': otrospagos})

        #********** DEDUCCIONES *********
        total_imp_ret = 0
        suma_deducciones = 0
        self.importe_isr = 0
        self.isr_periodo = 0
        no_deuducciones = 0 #len(self.deducciones_lines)
        deducciones_lines = self.env['hr.payslip.line'].search([('category_id.code','=','DED'),('slip_id','=',self.id),('total','>',0)])
        #ded_impuestos_lines = self.env['hr.payslip.line'].search([('category_id.name','=','Deducciones'),('code','=','301'),('slip_id','=',self.id)],limit=1)
        #tipo_deduccion_dict = dict(self.env['hr.salary.rule']._fields.get('tipo_deduccion').selection)
        #if ded_impuestos_lines:
        #   total_imp_ret = round(ded_impuestos_lines.total,2)
        lineas_deduccion = []
        if deducciones_lines:
            #_logger.info('entro deduciones ...')
            #todas las deducciones excepto imss e isr
            for line in deducciones_lines:
                if line.salary_rule_id.tipo_cdeduccion.clave != '001' and line.salary_rule_id.tipo_cdeduccion.clave != '002':
                    #_logger.info('linea  ...')
                    no_deuducciones += 1
                    lineas_deduccion.append({
                   'TipoDeduccion': line.salary_rule_id.tipo_cdeduccion.clave,
                   'Clave': line.code,
                   'Concepto': line.salary_rule_id.name,
                   'Importe': round(line.total,2)})
                    payslip_total_TDED += round(line.total,2)

            #todas las deducciones imss
            self.importe_imss = 0
            for line in deducciones_lines:
                if line.salary_rule_id.tipo_cdeduccion.clave == '001':
                    #_logger.info('linea imss ...')
                    self.importe_imss += round(line.total,2)

            if self.importe_imss > 0:
                no_deuducciones += 1
                self.calculo_imss()
                lineas_deduccion.append({'TipoDeduccion': '001',
                  'Clave': '302',
                  'Concepto': 'Seguridad social',
                  'Importe': round(self.importe_imss,2)})
                payslip_total_TDED += round(self.importe_imss,2)

            #todas las deducciones isr
            for line in deducciones_lines:
                if line.salary_rule_id.tipo_cdeduccion.clave == '002' and line.salary_rule_id.code == 'ISR':
                    self.isr_periodo = line.total 
                if line.salary_rule_id.tipo_cdeduccion.clave == '002':
                    #_logger.info('linea ISR ...')
                    self.importe_isr += round(line.total,2)

            if self.importe_isr > 0:
                no_deuducciones += 1
                lineas_deduccion.append({'TipoDeduccion': '002',
                  'Clave': '301',
                  'Concepto': 'ISR',
                  'Importe': round(self.importe_isr,2)})
                payslip_total_TDED += round(self.importe_isr,2)
            total_imp_ret = round(self.importe_isr,2)

        deduccion = {
            'TotalDeduccion': {
                    'TotalOtrasDeducciones': round(payslip_total_TDED - total_imp_ret,2),
                    'TotalImpuestosRetenidos': round(total_imp_ret,2),
            },
        }
        deduccion.update({'lineas_de_deduccion': lineas_deduccion, 'no_deuducciones': no_deuducciones})
        request_params.update({'deducciones': deduccion})

        #************ INCAPACIDADES  ************#
        incapacidades = self.env['hr.payslip.worked_days'].search([('payslip_id','=',self.id)])
        if incapacidades:
            for ext_line in incapacidades:
                if ext_line.code == 'INC_RT' or ext_line.code == 'INC_EG' or ext_line.code == 'INC_MAT':
                    _logger.info('codigo %s.... ', ext_line.code)
                    tipo_inc = ''
                    if ext_line.code == 'INC_RT':
                        tipo_inc = '01'
                    elif ext_line.code == 'INC_EG':
                        tipo_inc = '02'
                    elif ext_line.code == 'INC_MAT':
                        tipo_inc = '03'
                    incapacidad = {
                  'Incapacidad': {
                        'DiasIncapacidad': ext_line.number_of_days,
                        'TipoIncapacidad': tipo_inc,
                        'ImporteMonetario': 0,
                        },
                        }
                    request_params.update({'incapacidades': incapacidad})
        self.retencion_subsidio_pagado = self.isr_periodo - self.subsidio_periodo
        self.total_nomina = payslip_total_PERG + payslip_total_PERE + payslip_total_TOP - payslip_total_TDED
        self.subtotal =  payslip_total_PERG + payslip_total_PERE + payslip_total_TOP
        self.descuento = payslip_total_TDED
        work_days = 0
        lineas_trabajo = self.env['hr.payslip.worked_days'].search([('payslip_id','=',self.id)])
        for dias_pagados in lineas_trabajo:
            if dias_pagados.code == 'WORK100':
                work_days += dias_pagados.number_of_days
            if dias_pagados.code == 'FJC':
                work_days += dias_pagados.number_of_days
            if dias_pagados.code == 'SEPT':
                work_days += dias_pagados.number_of_days
        diaspagados = 0
        if self.struct_id.name == 'Reparto de utilidades':
            diaspagados = 365
        else:
            diaspagados = work_days
        contrato = 0
        if self.struct_id.name == 'Liquidación - indemnizacion/finiquito':
            regimen = '13'
            contrato = '99'
        else:
            regimen = self.employee_id.tipo_regimen
            contrato = self.employee_id.tipo_contrato
        cur_time = datetime.datetime.now(pytz.timezone(self.env.user.tz))
        cert = self.company_id.l10n_mx_edi_certificate_ids
        if not cert:
            raise UserError('No hay ningun certificado valido activo, contacta a soporte!')

        ###################
        #   XML CFDI 4.0  #
        ###################

        _logger.info(lineas_de_percepcion)
        _logger.info(lineas_de_percepcion_exentas)
        
        if total_imp_ret > 0:
            Deducciones = {
                'TotalOtrasDeducciones': str(round(payslip_total_TDED - total_imp_ret,2)) or '',
                'TotalImpuestosRetenidos': str(total_imp_ret) or ''
            }
        else:
            Deducciones = {
                'TotalOtrasDeducciones': str(round(payslip_total_TDED - total_imp_ret,2)) or '',
                'TotalImpuestosRetenidos': ''
            }

        data = {
            'Atributos': {
                'Fecha': cur_time.strftime("%Y-%m-%dT%H:%M:%S"),
                'Folio': self.number_folio or '',
                'SubTotal': str(round(self.subtotal,2)) or '',
                'Descuento': str(round(self.descuento,2)) or '',
                'Moneda': "MXN",
                'Total': str(round(self.total_nomina,2)) or '',
                'TipoDeComprobante': self.tipo_comprobante or 'N',
                'MetodoPago': self.methodo_pago or '',
                'LugarExpedicion': self.company_id.zip or '',
                'Exportacion': "01",
                'Certificado': cert.content.decode('utf-8') or '',
                'NoCertificado': cert.serial_number or '',
            },
            'Emisor': {
                'Rfc': self.company_id.vat, 
                'Nombre': self.company_id.name or '', 
                'RegimenFiscal': str(self.company_id.l10n_mx_edi_fiscal_regime) or ''
            },
            'Receptor': {
                'Rfc': self.employee_id.rfc or '',
                'Nombre': self.employee_id.name or '',
                'DomicilioFiscalReceptor': self.employee_id.zip or '',
                'RegimenFiscalReceptor': self.employee_id.regimen or '',
                'UsoCFDI': self.uso_cfdi or 'CN01'
            },
            #f'{diaspagados:.3f}'
            'Concepto':{
                'Cantidad': "1",
                'Descripcion': "Pago de nómina",
                'ValorUnitario': str(round(self.subtotal,2)) or '',
                'Importe': f'{round(self.subtotal,2):.2f}' or '',
                'ClaveProdServ':"84111505",
                'ClaveUnidad':"ACT",
                'Descuento': f'{round(self.descuento,2):.2f}',
                'ObjetoImp': "01"    
            },
            'Nomina': {
                'Version': "1.2",
                'TipoNomina': self.tipo_nomina or '',
                'FechaPago': fields.Date.to_string(self.fecha_pago) or '',
                'FechaInicialPago': fields.Date.to_string(self.date_from) or '',
                'FechaFinalPago': fields.Date.to_string(self.date_to) or '',
                'TotalPercepciones': str(round(payslip_total_PERG + payslip_total_PERE,2)),
                'NumDiasPagados': f'{diaspagados:.3f}' or '',
                'TotalDeducciones': str(round(self.descuento,2)) or '',
                'TotalOtrosPagos': str(round(payslip_total_TOP,2)),
            },
            'NEmisor': {
                'RegistroPatronal': self.employee_id.registro_patronal or '',
                'RfcPatronOrigen' : '', ##NECESITAMOS ESTE DATO CONFORME A LA DOCUMENTACION DEL SAT
            },
            'NReceptor': {
                'Curp': self.employee_id.curp or '',
                'NumSeguridadSocial': self.employee_id.segurosocial or '',
                'FechaInicioRelLaboral': fields.Date.to_string(self.contract_id.date_start) or '',
                'Antigüedad': 'P' + f'{antiguedad:.0f}' + 'W',
                'TipoContrato': contrato,
                'TipoJornada': str(self.employee_id.jornada),
                'TipoRegimen': self.employee_id.tipo_regimen,
                'NumEmpleado': self.employee_id.no_empleado or '',
                'Departamento': '',##NECESITAMOS ESTE DATO CONFORME A LA DOCUMENTACION DEL SAT
                'Puesto': '',##NECESITAMOS ESTE DATO CONFORME A LA DOCUMENTACION DEL SAT
                'RiesgoPuesto': str(self.contract_id.riesgo_puesto) or '',
                'PeriodicidadPago': str(self.contract_id.periodicidad_pago) or '',
                'CuentaBancaria': '',##NECESITAMOS ESTE DATO CONFORME A LA DOCUMENTACION DEL SAT
                'Banco': '',##NECESITAMOS ESTE DATO CONFORME A LA DOCUMENTACION DEL SAT
                'SalarioBaseCotApor': str(round(self.contract_id.sueldo_base_cotizacion,2)) or '',
                'SalarioDiarioIntegrado': str(round(self.contract_id.sueldo_diario_integrado,2)) or '',
                'ClaveEntFed': self.employee_id.estado.code or '',   
            },
            'Percepciones': {
                'TotalSueldos': str(round(payslip_total_PERG + payslip_total_PERE,2)),
                'TotalGravado': str(round(payslip_total_PERG,2)),
                'TotalExento': str(round(payslip_total_PERE,2)),
            },
            'Percepcion':{
                'Percepcion': lineas_de_percepcion,
                'PercepcionExc': lineas_de_percepcion_exentas,
            },
            'Deducciones': Deducciones,
            'Deduccion': lineas_deduccion,
            'OtrosPagos': lineas_de_otros,
            
        }

        comprobante = Element('cfdi:Comprobante',
                            {
                                'xmlns:cfdi': "http://www.sat.gob.mx/cfd/4",
                                'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
                                'xmlns:nomina12': "http://www.sat.gob.mx/nomina12", 
                                'xsi:schemaLocation':  "http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd http://www.sat.gob.mx/nomina12 http://www.sat.gob.mx/sitio_internet/cfd/nomina/nomina12.xsd",
                                'Version': "4.0",
                                'Fecha': cur_time.strftime("%Y-%m-%dT%H:%M:%S"), #+ 'T00:00:00',
                                #'Serie': self.company_id.serie_nomina or '',
                                'Folio': self.number_folio or '',
                                'SubTotal': str(round(self.subtotal,2)) or '',
                                'Descuento': str(round(self.descuento,2)) or '',
                                'Moneda': "MXN",
                                'Total': str(round(self.total_nomina,2)) or '',
                                'TipoDeComprobante': self.tipo_comprobante or 'N',
                                'MetodoPago': self.methodo_pago or '',
                                'LugarExpedicion': self.company_id.zip or '',
                                'Exportacion': "01",
                                'Certificado': cert.content.decode('utf-8') or '',
                                'NoCertificado': cert.serial_number or '',
                                'Sello': '',
                            }
        )
        emisor = SubElement(comprobante, 'cfdi:Emisor',{'Rfc': self.company_id.vat, 'Nombre': self.company_id.name or '', 'RegimenFiscal': str(self.company_id.l10n_mx_edi_fiscal_regime) or ''})
        receptor = SubElement(comprobante, 'cfdi:Receptor', {
            'Rfc': self.employee_id.rfc or '',
            'Nombre': self.employee_id.name or '',
            'DomicilioFiscalReceptor': self.employee_id.zip or '',
            'RegimenFiscalReceptor': self.employee_id.regimen or '',
            'UsoCFDI': 'CN01'
            })
        conceptos = SubElement(comprobante, 'cfdi:Conceptos')
        concepto = SubElement(conceptos,'cfdi:Concepto', {
            'Cantidad': "1",
            'Descripcion': "Pago de nómina",
            'ValorUnitario': str(round(self.subtotal,2)) or '',
            'Importe': str(round(self.subtotal,2)) or '',
            'ClaveProdServ':"84111505",
            'ClaveUnidad':"ACT",
            'Descuento': str(round(self.descuento,2)),
            'ObjetoImp': "01"            
        })
        complemento = SubElement(comprobante,'cfdi:Complemento')
        nomina12 = SubElement(complemento, 'nomina12:Nomina', {
            'Version': "1.2",
            'TipoNomina': self.tipo_nomina or '',
            'FechaPago': fields.Date.to_string(self.fecha_pago) or '',
            'FechaInicialPago': fields.Date.to_string(self.date_from) or '',
            'FechaFinalPago': fields.Date.to_string(self.date_to) or '',
            'TotalPercepciones': str(round(payslip_total_PERG + payslip_total_PERE,2)),
            'NumDiasPagados': f'{diaspagados:.3f}' or '',
            'TotalDeducciones': str(round(self.descuento,2)) or '',
            'TotalOtrosPagos': str(round(payslip_total_TOP,2)),
        })
        n12emisor = SubElement(nomina12,'nomina12:Emisor',{'RegistroPatronal': self.employee_id.registro_patronal or ''})
        n12receptor = SubElement(nomina12,'nomina12:Receptor',{
            'Curp': self.employee_id.curp or '',
            'NumSeguridadSocial': self.employee_id.segurosocial or '',
            'FechaInicioRelLaboral': fields.Date.to_string(self.contract_id.date_start) or '',
            'Antigüedad': 'P' + f'{antiguedad:.0f}' + 'W',
            'TipoContrato': contrato or '',
            #'Sindicalizado': "No",
            'TipoJornada': str(self.employee_id.jornada),
            'TipoRegimen': self.employee_id.tipo_regimen,
            'NumEmpleado': self.employee_id.no_empleado or '',
            'RiesgoPuesto': str(self.contract_id.riesgo_puesto) or '',
            'PeriodicidadPago': str(self.contract_id.periodicidad_pago) or '',
            'SalarioBaseCotApor': str(round(self.contract_id.sueldo_base_cotizacion,2)) or '',
            'SalarioDiarioIntegrado': str(round(self.contract_id.sueldo_diario_integrado,2)) or '',
            'ClaveEntFed': self.employee_id.estado.code or '',
        })
        n12percepciones = SubElement(nomina12,'nomina12:Percepciones',{
            'TotalSueldos': str(round(payslip_total_PERG + payslip_total_PERE,2)),
            'TotalGravado': str(round(payslip_total_PERG,2)),
            'TotalExento': str(round(payslip_total_PERE,2)),
        })

        for l in lineas_de_percepcion:
            n12perg = SubElement(n12percepciones,'nomina12:Percepcion',{
                'TipoPercepcion': l['TipoPercepcion'] or '',
                'Clave': l['Clave'] or '',
                'Concepto': l['Concepto'] or '',
                'ImporteGravado': str(l['ImporteGravado']) or '',
                'ImporteExento': str(l['ImporteExento']) or ''
            })        
        for r in lineas_de_percepcion_exentas:
            n12pere = SubElement(n12percepciones,'nomina12:Percepcion',{
                'TipoPercepcion': r['TipoPercepcion'] or '',
                'Clave': r['Clave'] or '',
                'Concepto': r['Concepto'] or '',
                'ImporteGravado': str(r['ImporteGravado']) or '',
                'ImporteExento': str(r['ImporteExento']) or ''
            })
        
        if total_imp_ret > 0:
            n12deducciones = SubElement(nomina12,'nomina12:Deducciones',{
                'TotalOtrasDeducciones': str(round(payslip_total_TDED - total_imp_ret,2)) or '',
                'TotalImpuestosRetenidos': str(round(total_imp_ret,2)) or ''
            })
        else:
            n12deducciones = SubElement(nomina12,'nomina12:Deducciones',{
                'TotalOtrasDeducciones': str(round(payslip_total_TDED - total_imp_ret,2)) or ''
            })            
        for d in lineas_deduccion:
            n12ded = SubElement(n12deducciones,'nomina12:Deduccion',{
                'TipoDeduccion': d['TipoDeduccion'] or '',
                'Clave': d['Clave'] or '',
                'Concepto': d['Concepto'] or '',
                'Importe': str(d['Importe']) or ''
            })

        n12otrospagos = SubElement(nomina12,'nomina12:OtrosPagos')
        for o in lineas_de_otros:
            n12otr = SubElement(n12otrospagos,'nomina12:OtroPago',{
                'TipoOtroPago': o['TipoOtrosPagos'] or '',
                'Clave': o['Clave'] or '',
                'Concepto': o['Concepto'] or '',
                'Importe': str(o['ImporteExento']) or ''
            })
            if o['TipoOtrosPagos'] == '002':
                subs = SubElement(n12otr,'nomina12:SubsidioAlEmpleo',{
                    'SubsidioCausado': str(o['ImporteExento']) or ''
                })
        
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(
                    os.path.dirname(os.path.abspath(
                        __file__)), '../template',),),
            undefined=StrictUndefined, autoescape=True,
        )
        template = env.get_template('nomina.jinja')
        xml_j = template.render(data=data).encode('utf-8')
        _logger.info("xml")
        _logger.info(xml_j)

        xml_comp = ElementTree(comprobante)
        f = BytesIO()
        xml_comp.write(f, encoding='UTF-8', xml_declaration=False) 
        xml_comprobante = f.getvalue()
        print(xml_comprobante)
        
        all_paths = tools.config["addons_path"].split(",")
        for my_path in all_paths:
            if os.path.isdir(os.path.join(my_path, 'nomina_cfdi', 'data')):
                path_cadena = os.path.join(
                    my_path, 'nomina_cfdi', 'data', 'cadenaoriginal_4_0.xslt')
                continue
        
        #GENERAMOS CADENA ORIGINAL
        #cadena = self.generate_cadena_original(
        #        xml_comprobante, {'path_cadena': path_cadena})
        cadena = self.generate_cadena_original(
                xml_j, {'path_cadena': path_cadena})
        print("CADENA")
        print(cadena)        
        
        #GENERAMOS SELLO
        certificate_ids = self.company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        if not certificate_id:
            return cfdi
        sello = certificate_id.sudo().get_encrypted_cadena(cadena)
        print("SELLO")
        print(sello)
        #tree = objectify.fromstring(xml_comprobante)
        tree = objectify.fromstring(xml_j)
        
        #AÑADIMOS SELLO A NUESTRO XML
        tree.attrib['Sello'] = sello.decode("utf-8") 
        xml = etree.tostring(
                tree, pretty_print=False,
                xml_declaration=False, encoding='UTF-8')
        print("CADENA CON SELLO")
        print(type(xml))
        print(xml)

        if self.company_id.l10n_mx_edi_pac_test_env:
            pac_url = "https://testing.solucionfactible.com/ws/services/Timbrado?wsdl"
            pac_usr = 'testing@solucionfactible.com'
            pac_pwd = 'timbrado.SF.16672'
        else:
            pac_url = 'https://solucionfactible.com/ws/services/Timbrado?wsdl'
            pac_usr = self.company_id.l10n_mx_edi_pac_username
            pac_pwd = self.company_id.l10n_mx_edi_pac_password
                    
        #TIMBRAMOS
        transport = Transport(timeout=20)
        client = Client(pac_url, transport=transport)
        response = client.service.timbrar(pac_usr, pac_pwd, xml, False)
        
        print("response")
        print(response)

        ##### MOD-2 RETORNAMOS LA RESPUESTA
        return response

        #raise UserError(f.getvalue())
        #with open('/mnt/extra-addons/comprobante.xml', 'w') as f:
        #    f.write(str(xml_comprobante))

        #####CODIGO ANTERIOR COMENTADO POR EL MOMENTO
        #base64_cfdi = base64.b64encode(xml)
#
        #if self.company_id.l10n_mx_edi_pac_test_env:
        #    user = 'testing@solucionfactible.com'
        #    pwd = 'timbrado.SF.16672'
        #else:
        #    user = self.company_id.l10n_mx_edi_pac_username
        #    pwd = self.company_id.l10n_mx_edi_pac_password
#
        #b64 = base64_cfdi.decode('utf-8')
#
        #req = Element('soapenv:Envelope',{
        #    'xmlns:soapenv': "http://schemas.xmlsoap.org/soap/envelope/",
        #    'xmlns:xsd': "http://www.w3.org/2001/XMLSchema",
        #    'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
        #})
        #body = SubElement(req,'soapenv:Body')
        #timbrar = SubElement(body,'timbrar',{'xmlns':"http://timbrado.ws.cfdi.solucionfactible.com"})
        #usuario = SubElement(timbrar,'usuario')
        #usuario.text = user
        #password = SubElement(timbrar,'password')
        #password.text = pwd
        #cfdi = SubElement(timbrar,'cfdi')
        #cfdi.text = b64 or ''
        #zip = SubElement(timbrar,'zip')
        #zip.text = 'false'
#
        #xml_req = ElementTree(req)
        #fr = BytesIO()
        #xml_req.write(fr, encoding='UTF-8', xml_declaration=True) 
        #xml_request = fr.getvalue()
        ##raise UserError(xml_request)
        ##with open('/mnt/extra-addons/request.xml', 'w') as f:
        ##    f.write(xml_request)
        #return xml_request

    @classmethod
    def generate_cadena_original(self, xml, context=None):
        xlst_file = tools.file_open(context.get('path_cadena', '')).name
        dom = etree.fromstring(xml)
        xslt = etree.parse(xlst_file)
        transform = etree.XSLT(xslt)
        return str(transform(dom))

    def action_cfdi_nomina_generate(self):
        for payslip in self:
            if payslip.fecha_factura == False:
                payslip.fecha_factura= datetime.datetime.now()
                payslip.write({'fecha_factura': payslip.fecha_factura})
            if payslip.estado_factura == 'factura_correcta':
                raise UserError(_('Error para timbrar factura, Factura ya generada.'))
            if payslip.estado_factura == 'factura_cancelada':
                raise UserError(_('Error para timbrar factura, Factura ya generada y cancelada.'))

            values = payslip.build_xml()
            print(values)
            print(values.status)

            ##### MOD-2 RETORNAMOS LA RESPUESTA
            resultadoTimbrado = values.resultados[0]
            if resultadoTimbrado['status'] == 200:
                xml_file_name = payslip.number.replace('/','_') + '.xml'
                self.env['ir.attachment'].sudo().create({
                                                            'name': xml_file_name,
                                                            'datas': base64.b64encode(resultadoTimbrado['cfdiTimbrado']),
                                                            'res_model': self._name,
                                                            'res_id': payslip.id,
                                                            'type': 'binary'
                                                        })	

                payslip.folio_fiscal = resultadoTimbrado['uuid']
                payslip.estado_factura = 'factura_correcta'
                payslip.fecha_factura = resultadoTimbrado['fechaTimbrado'].date()
                payslip.cadena_origenal = resultadoTimbrado['cadenaOriginal']
                payslip.cetificaso_sat = resultadoTimbrado['certificadoSAT']
                payslip.fecha_certificacion = resultadoTimbrado['fechaTimbrado'].date()
                payslip.selo_sat = resultadoTimbrado['selloSAT']
                payslip.folio_fiscal = resultadoTimbrado['uuid']
                payslip.version = resultadoTimbrado['versionTFD']

                payslip.qrcode_image = base64.b64encode(resultadoTimbrado['qrCode'])

                dict_data = dict(xmltodict.parse(resultadoTimbrado['cfdiTimbrado']).get('cfdi:Comprobante', {}))
                tfd = dict_data

                sello = tfd.get('@Sello', '')
                no_certificado = tfd.get('@NoCertificado', '')
                payslip.numero_cetificado = no_certificado
                payslip.selo_digital_cdfi = sello

                ## MOD-2 MANDAMOS A PAGADO
                payslip.nomina_cfdi = True
                payslip.action_payslip_paid()
                """report = self.env['ir.actions.report']._get_report_from_name('nomina_cfdi.report_payslip')
                report_data = report._render([payslip.id])[0]
                pdf_file_name = payslip.number.replace('/','_') + '.pdf'
                self.env['ir.attachment'].with_user(self.env.ref('base.user_admin')).create(
                                            {
                                                'name': pdf_file_name,
                                                'datas': base64.b64encode(report_data),
                                                'res_model': self._name,
                                                'res_id': payslip.id,
                                                'type': 'binary'
                                            }) """
            else:
                raise UserError("Mensaje: " + resultadoTimbrado['mensaje'])

                #raise UserError("Codigo: "+str(resultadoTimbrado.status)+"\n"+"Descr: "+ resultadoTimbrado.mensaje)       


            """_logger.info('something ... %s', response.text)
            json_response = response.json()
            xml_file_link = False
            estado_factura = json_response['estado_factura']
            if estado_factura == 'problemas_factura':
                raise UserError(_(json_response['problemas_message']))
            # Receive and stroe XML 
            if json_response.get('factura_xml'):
                xml_file_link = payslip.company_id.factura_dir + '/' + payslip.number.replace('/','_') + '.xml'
                xml_file = open(xml_file_link, 'w')
                xml_payment = base64.b64decode(json_response['factura_xml'])
                xml_file.write(xml_payment.decode("utf-8"))
                xml_file.close()
                payslip._set_data_from_xml(xml_payment)
                    
                xml_file_name = payslip.number.replace('/','_') + '.xml'
                self.env['ir.attachment'].sudo().create(
                                            {
                                                'name': xml_file_name,
                                                'datas': json_response['factura_xml'],
                                                'datas_fname': xml_file_name,
                                                'res_model': self._name,
                                                'res_id': payslip.id,
                                                'type': 'binary'
                                            })	
                report = self.env['ir.actions.report']._get_report_from_name('nomina_cfdi.report_payslip')
                report_data = report.render_qweb_pdf([payslip.id])[0]
                pdf_file_name = payslip.number.replace('/','_') + '.pdf'
                self.env['ir.attachment'].sudo().create(
                                            {
                                                'name': pdf_file_name,
                                                'datas': base64.b64encode(report_data),
                                                'datas_fname': pdf_file_name,
                                                'res_model': self._name,
                                                'res_id': payslip.id,
                                                'type': 'binary'
                                            })

            payslip.write({'estado_factura': estado_factura,
                    'xml_nomina_link': xml_file_link,
                    'nomina_cfdi': True}) """

    def _set_data_from_xml(self, xml_invoice):
        if not xml_invoice:
            return None
        NSMAP = {
                 'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                 'cfdi':'http://www.sat.gob.mx/cfd/3', 
                 'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                 }

        xml_data = etree.fromstring(xml_invoice)
        Emisor = xml_data.find('cfdi:Emisor', NSMAP)
        RegimenFiscal = Emisor.find('cfdi:RegimenFiscal', NSMAP)
        Complemento = xml_data.find('cfdi:Complemento', NSMAP)
        TimbreFiscalDigital = Complemento.find('tfd:TimbreFiscalDigital', NSMAP)
        
        self.rfc_emisor = Emisor.attrib['Rfc']
        self.name_emisor = Emisor.attrib['Nombre']
        self.tipocambio = xml_data.attrib['TipoCambio']
        #  self.tipo_comprobante = xml_data.attrib['TipoDeComprobante']
        self.moneda = xml_data.attrib['Moneda']
        self.numero_cetificado = xml_data.attrib['NoCertificado']
        self.cetificaso_sat = TimbreFiscalDigital.attrib['NoCertificadoSAT']
        self.fecha_certificacion = TimbreFiscalDigital.attrib['FechaTimbrado']
        self.selo_digital_cdfi = TimbreFiscalDigital.attrib['SelloCFD']
        self.selo_sat = TimbreFiscalDigital.attrib['SelloSAT']
        self.folio_fiscal = TimbreFiscalDigital.attrib['UUID']
        if self.number:
            self.folio = xml_data.attrib['Folio']
        if self.company_id.serie_nomina:
            self.serie_emisor = xml_data.attrib['Serie']
        self.invoice_datetime = xml_data.attrib['Fecha']
        self.version = TimbreFiscalDigital.attrib['Version']
        self.cadena_origenal = '||%s|%s|%s|%s|%s||' % (self.version, self.folio_fiscal, self.fecha_certificacion, 
                                                         self.selo_digital_cdfi, self.cetificaso_sat)
        
        options = {'width': 275 * mm, 'height': 275 * mm}
        amount_str = str(self.total_nomina).split('.')
        #print 'amount_str, ', amount_str
        qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (self.folio_fiscal,
                                                 self.company_id.rfc, 
                                                 self.employee_id.rfc,
                                                 amount_str[0].zfill(10),
                                                 amount_str[1].ljust(6, '0'),
                                                 self.selo_digital_cdfi[-8:],
                                                 )
        self.qr_value = qr_value
        ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
        self.qrcode_image = base64.encodestring(ret_val.asString('jpg'))

    """ def action_cfdi_cancel(self):
        for payslip in self:
            if payslip.nomina_cfdi:
                if payslip.estado_factura == 'factura_cancelada':
                    pass
                    # raise UserError(_('La factura ya fue cancelada, no puede volver a cancelarse.'))
                if not payslip.company_id.archivo_cer:
                    raise UserError(_('Falta la ruta del archivo .cer'))
                if not payslip.company_id.archivo_key:
                    raise UserError(_('Falta la ruta del archivo .key'))
                archivo_cer = payslip.company_id.archivo_cer
                archivo_key = payslip.company_id.archivo_key
                archivo_xml_link = payslip.company_id.factura_dir + '/' + payslip.number.replace('/','_') + '.xml'
                with open(archivo_xml_link, 'rb') as cf:
                    archivo_xml = base64.b64encode(cf.read())
                values = {
                          'rfc': payslip.company_id.rfc,
                          'api_key': payslip.company_id.proveedor_timbrado,
                          'uuid': self.folio_fiscal,
                          'folio': self.folio,
                          'serie_factura': payslip.company_id.serie_nomina,
                          'modo_prueba': payslip.company_id.modo_prueba,
                            'certificados': {
                                  'archivo_cer': archivo_cer.decode("utf-8"),
                                  'archivo_key': archivo_key.decode("utf-8"),
                                  'contrasena': payslip.company_id.contrasena,
                            },
                          'xml': archivo_xml.decode("utf-8"),
                          }
                if self.company_id.proveedor_timbrado == 'multifactura':
                    url = '%s' % ('http://facturacion.itadmin.com.mx/api/refund')
                elif self.company_id.proveedor_timbrado == 'multifactura2':
                    url = '%s' % ('http://facturacion2.itadmin.com.mx/api/refund')
                elif self.company_id.proveedor_timbrado == 'multifactura3':
                    url = '%s' % ('http://facturacion3.itadmin.com.mx/api/refund')
                elif self.company_id.proveedor_timbrado == 'gecoerp':
                    if self.company_id.modo_prueba:
                        url = '%s' % ('https://ws.gecoerp.com/itadmin/pruebas/refund/?handler=OdooHandler33')
                        #url = '%s' % ('https://itadmin.gecoerp.com/refund/?handler=OdooHandler33')
                    else:
                        url = '%s' % ('https://itadmin.gecoerp.com/refund/?handler=OdooHandler33')
                response = requests.post(url , 
                                         auth=None,verify=False, data=json.dumps(values), 
                                         headers={"Content-type": "application/json"})
    
                #print 'Response: ', response.status_code
                json_response = response.json()
                #_logger.info('log de la exception ... %s', response.text)

                if json_response['estado_factura'] == 'problemas_factura':
                    raise UserError(_(json_response['problemas_message']))
                elif json_response.get('factura_xml', False):
                    if payslip.number:
                        xml_file_link = payslip.company_id.factura_dir + '/CANCEL_' + payslip.number.replace('/','_') + '.xml'
                    else:
                        raise UserError(_('La nómina no tiene nombre'))
                    xml_file = open(xml_file_link, 'w')
                    xml_invoice = base64.b64decode(json_response['factura_xml'])
                    xml_file.write(xml_invoice.decode("utf-8"))
                    xml_file.close()
                    if payslip.number:
                        file_name = payslip.number.replace('/','_') + '.xml'
                    else:
                        file_name = self.number.replace('/','_') + '.xml'
                    self.env['ir.attachment'].sudo().create(
                                                {
                                                    'name': file_name,
                                                    'datas': json_response['factura_xml'],
                                                    'datas_fname': file_name,
                                                    'res_model': self._name,
                                                    'res_id': payslip.id,
                                                    'type': 'binary'
                                                })
                payslip.write({'estado_factura': json_response['estado_factura']}) """

    ##METODO PARA CANCELAR
    def cfdi_etree(self):
        fname = '%s.xml' % (self.number.replace('/', '_'))
        att_xml_id = self.env['ir.attachment'].search([
            ('name', '=', fname),
            ('res_model', '=', 'hr.payslip'),
            ('res_id', '=', self.id),
        ], limit=1)
        if not len(att_xml_id) >= 1:
            return False
        return objectify.fromstring(base64.b64decode(att_xml_id.datas))
    
    @api.model
    def _get_stamp_data(self, cfdi):
        self.ensure_one()
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    def action_cfdi_cancel(self):
        msg = ''
        folio_cancel = ''
        
        if self.company_id.l10n_mx_edi_pac_test_env:
            pac_url = "https://testing.solucionfactible.com/ws/services/Timbrado?wsdl"
            pac_usr = 'testing@solucionfactible.com'
            pac_pwd = 'timbrado.SF.16672'
        else:
            pac_url = 'https://solucionfactible.com/ws/services/Timbrado?wsdl'
            pac_usr = self.company_id.l10n_mx_edi_pac_username
            pac_pwd = self.company_id.l10n_mx_edi_pac_password
    
        certificate_id = self.company_id.l10n_mx_edi_certificate_ids
        cer_pem = certificate_id.get_pem_cer(certificate_id.content)
        key_pem = certificate_id.get_pem_key(
            certificate_id.key, certificate_id.password)
        xml = self.cfdi_etree()
        tfd_node = self._get_stamp_data(xml)
        if self.uuid_replace_cancel:
            u_cancel = self.uuid_replace_cancel
        else:
            u_cancel = ""
        #folio_cancel = tfd_node.get('UUID') + "|" + self.type_cancel + "|" + u_cancel
        if self.type_cancel:
            if tfd_node:
                folio_cancel = tfd_node.get('UUID') + "|" + self.type_cancel + "|" + u_cancel
            else:
                folio_cancel = self.folio_fiscal + "|" + self.type_cancel + "|" + u_cancel
            #raise UserError(folio_cancel)
            uuids = [folio_cancel]
            try:
                transport = Transport(timeout=20)
                client = Client(pac_url, transport=transport)
                result = client.service.cancelar(
                    pac_usr, pac_pwd, uuids, cer_pem, key_pem, certificate_id.password)
            except Exception as e:
                self.message_post(body=_(
                    'Revisa tu conexion a internet y los datos del PAC'))
                return False
            res = result.resultados
            code = getattr(res[0], 'statusUUID', None) if res else getattr(
                response, 'status', None)
            cancelled = code in ('201', '202')
            msg = '' if cancelled else getattr(
                res[0] if res else response, 'mensaje', None)
            code = '' if cancelled else code
            if cancelled:
                self.message_post(
                    body=_('\n- El proceso de cancelación se ha completado correctamente.'))
                self.estado_factura = 'factura_cancelada'
                self.state = 'done'
            else:
                self.message_post(body=_('Mensaje %s\nCode: %s') % (msg, code))
        else:
            raise ValidationError('Para cancelar debe elegir primero un tipo de cancelacion')        

    def send_nomina(self):
        self.ensure_one()
        template = self.env.ref('nomina_cfdi.email_template_payroll', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        attachment = self.env['ir.attachment'].search([('res_id', '=', self.id), ('res_model','=','hr.payslip'),('name','ilike','.xml')])
        if attachment:    
            new_attachment = attachment[-1].copy()
            template.attachment_ids = new_attachment
        else:
            template.attachment_ids = [(3, template.attachment_ids.id)]

        ctx = dict(
            default_model='hr.payslip',
            default_res_id=self.id,
            default_res_model='hr.payslip',
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            force_email=True,
            active_ids=self.ids,
        )
        
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
        
    """ def send_nomina(self):
        self.ensure_one()
        template = self.env.ref('nomina_cfdi.email_template_payroll', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
            
        ctx = dict()
        ctx.update({
            'default_model': 'hr.payslip',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        } """

    @api.model
    def fondo_ahorro(self):	
        deducciones_ahorro = self.env['hr.payslip.line'].search([('category_id.code','=','DED'),('slip_id','=',self.id)])
        if deducciones_ahorro:
            _logger.info('fondo ahorro deudccion...')
            for line in deducciones_ahorro:
                if line.salary_rule_id.tipo_cdeduccion.clave == '017':
                    self.employee_id.fondo_ahorro += line.total

        percepciones_ahorro = self.env['hr.payslip.line'].search([('category_id.code','=','ALW2'),('slip_id','=',self.id)])
        if percepciones_ahorro:
            _logger.info('fondo ahorro percepcion...')
            for line in percepciones_ahorro:
                if line.salary_rule_id.tipo_cpercepcion.clave == '005':
                    self.employee_id.fondo_ahorro -= line.total

    @api.model
    def devolucion_fondo_ahorro(self):	
        deducciones_ahorro = self.env['hr.payslip.line'].search([('category_id.code','=','DED'),('slip_id','=',self.id)])
        if deducciones_ahorro:
            _logger.info('Devolucion fondo ahorro deduccion...')
            for line in deducciones_ahorro:
                if line.salary_rule_id.tipo_cdeduccion.clave == '017':
                    self.employee_id.fondo_ahorro -= line.total

        percepciones_ahorro = self.env['hr.payslip.line'].search([('category_id.code','=','ALW2'),('slip_id','=',self.id)])
        if percepciones_ahorro:
            _logger.info('Devolucion fondo ahorro percepcion...')
            for line in percepciones_ahorro:
                if line.salary_rule_id.tipo_cpercepcion.clave == '005':
                    self.employee_id.fondo_ahorro += line.total

    def action_payslip_done(self):
        res = super(HrPayslip,self).action_payslip_done()
        for rec in self:
            rec.fondo_ahorro()
        return res

    def refund_sheet(self):
        res = super(HrPayslip, self).refund_sheet()
        for rec in self:
            rec.devolucion_fondo_ahorro()
        return res

    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        for rec in self:
            rec.calculo_imss()
        return res

    @api.model
    def calculo_imss(self):
        #cuota del IMSS parte del Empleado
        dias_laborados = 0
        dias_completos = 0
        dias_falta = 0
        dias_trabajo = 0

        dias_completos = self.imss_dias
        dias_laborados =  dias_completos
        dias_falta =  dias_completos

        dias_registrados = self.env['hr.payslip.worked_days'].search([('payslip_id','=',self.id)])
        if dias_registrados:
            for dias in dias_registrados:
                if dias.code == 'FI' or dias.code == 'FJS':
                    dias_laborados = dias_laborados - dias.number_of_days
                    dias_falta = dias_falta - dias.number_of_days
                if dias.code == 'INC_MAT' or dias.code == 'INC_EG' or dias.code == 'INC_RT':
                    dias_laborados = dias_laborados - dias.number_of_days
                    dias_completos = dias_completos - dias.number_of_days
                if dias.code == 'WORK100' or dias.code == 'FJC' or dias.code == 'SEPT':
                    dias_trabajo = dias_trabajo + dias.number_of_days
        if dias_trabajo == 0:
            dias_laborados = 0
            dias_completos = 0

        #salario_cotizado = self.contract_id.sueldo_base_cotizacion
        base_calculo = 0
        base_execente = 0
        if self.contract_id.sueldo_base_cotizacion < 25 * self.contract_id.tablas_cfdi_id.uma:
            base_calculo = self.contract_id.sueldo_base_cotizacion
        else:
            base_calculo = 25 * self.contract_id.tablas_cfdi_id.uma

        if base_calculo > 3 * self.contract_id.tablas_cfdi_id.uma:
            base_execente = base_calculo - 3 * self.contract_id.tablas_cfdi_id.uma

        calcular_imss = self.env['hr.payslip.line'].search([('salary_rule_id.name','=','IMSS'),('slip_id','=',self.id)])

        if calcular_imss:
            #imss empleado
            self.emp_exedente_smg = round(dias_completos * self.contract_id.tablas_cfdi_id.enf_mat_excedente_e/100 * base_execente,2)
            self.emp_prest_dinero = round(dias_completos * self.contract_id.tablas_cfdi_id.enf_mat_prestaciones_e/100 * base_calculo,2)
            self.emp_esp_pens = round(dias_completos * self.contract_id.tablas_cfdi_id.enf_mat_gastos_med_e/100 * base_calculo,2)
            self.emp_invalidez_vida = round(dias_laborados * self.contract_id.tablas_cfdi_id.inv_vida_e/100 * base_calculo,2)
            self.emp_cesantia_vejez = round(dias_laborados * self.contract_id.tablas_cfdi_id.cesantia_vejez_e/100 * base_calculo,2)
            self.emp_total = self.emp_exedente_smg + self.emp_prest_dinero + self.emp_esp_pens + self.emp_invalidez_vida + self.emp_cesantia_vejez
            
            #imss patronal
            factor_riesgo = 0
            if self.contract_id.riesgo_puesto == '1':
                factor_riesgo = self.contract_id.tablas_cfdi_id.rt_clase1
            elif self.contract_id.riesgo_puesto == '2':
                factor_riesgo = self.contract_id.tablas_cfdi_id.rt_clase2
            elif self.contract_id.riesgo_puesto == '3':
                factor_riesgo = self.contract_id.tablas_cfdi_id.rt_clase3
            elif self.contract_id.riesgo_puesto == '4':
                factor_riesgo = self.contract_id.tablas_cfdi_id.rt_clase4
            elif self.contract_id.riesgo_puesto == '5':
                factor_riesgo = self.contract_id.tablas_cfdi_id.rt_clase5
            self.pat_cuota_fija_pat = round(dias_completos * self.contract_id.tablas_cfdi_id.enf_mat_cuota_fija/100 * self.contract_id.tablas_cfdi_id.uma,2)
            self.pat_exedente_smg =round(dias_completos * self.contract_id.tablas_cfdi_id.enf_mat_excedente_p/100 * base_execente,2)
            self.pat_prest_dinero = round(dias_completos * self.contract_id.tablas_cfdi_id.enf_mat_prestaciones_p/100 * base_calculo,2)
            self.pat_esp_pens = round(dias_completos * self.contract_id.tablas_cfdi_id.enf_mat_gastos_med_p/100 * base_calculo,2)
            self.pat_riesgo_trabajo = round(dias_laborados * factor_riesgo/100 * base_calculo,2) # falta
            self.pat_invalidez_vida = round(dias_laborados * self.contract_id.tablas_cfdi_id.inv_vida_p/100 * base_calculo,2)
            self.pat_guarderias = round(dias_laborados * self.contract_id.tablas_cfdi_id.guarderia_p/100 * base_calculo,2)
            self.pat_retiro = round(dias_falta * self.contract_id.tablas_cfdi_id.retiro_p/100 * base_calculo,2)
            self.pat_cesantia_vejez = round(dias_laborados * self.contract_id.tablas_cfdi_id.cesantia_vejez_p/100 * base_calculo,2)
            self.pat_infonavit = round(dias_falta * self.contract_id.tablas_cfdi_id.apotacion_infonavit/100 * base_calculo,2)
            self.pat_total = self.pat_cuota_fija_pat + self.pat_exedente_smg + self.pat_prest_dinero + self.pat_esp_pens + self.pat_riesgo_trabajo + self.pat_invalidez_vida + self.pat_guarderias + self.pat_retiro + self.pat_cesantia_vejez + self.pat_infonavit
        else:
            #imss empleado
            self.emp_exedente_smg = 0
            self.emp_prest_dinero = 0
            self.emp_esp_pens = 0
            self.emp_invalidez_vida = 0
            self.emp_cesantia_vejez = 0
            self.emp_total = 0
            
            #imss patronal
            self.pat_cuota_fija_pat = 0
            self.pat_exedente_smg =0
            self.pat_prest_dinero = 0
            self.pat_esp_pens = 0
            self.pat_riesgo_trabajo = 0
            self.pat_invalidez_vida = 0
            self.pat_guarderias = 0
            self.pat_retiro = 0
            self.pat_cesantia_vejez = 0
            self.pat_infonavit = 0
            self.pat_total = 0

class HrPayslipMail(models.Model):
    _name = "hr.payslip.mail"
    _inherit = ['mail.thread']
    _description = "Nomina Mail"
   
    payslip_id = fields.Many2one('hr.payslip', string='Nomina')
    name = fields.Char(related='payslip_id.name')
    xml_nomina_link = fields.Char(related='payslip_id.xml_nomina_link')
    employee_id = fields.Many2one(related='payslip_id.employee_id')
    company_id = fields.Many2one(related='payslip_id.company_id')
    
class MailTemplate(models.Model):
    "Templates for sending email"
    _inherit = 'mail.template'
    
    @api.model
    def _get_file(self, url):
        url = url.encode('utf8')
        filename, headers = urllib.urlretrieve(url)
        fn, file_extension = os.path.splitext(filename)
        return  filename, file_extension.replace('.', '')

    """ def generate_email(self, res_ids, fields=None):
        results = super(MailTemplate, self).generate_email(res_ids, fields=fields)
        
        if isinstance(res_ids, (int)):
            res_ids = [res_ids]
        res_ids_to_templates = super(MailTemplate, self).get_email_template(res_ids)

        # templates: res_id -> template; template -> res_ids
        templates_to_res_ids = {}
        for res_id, template in res_ids_to_templates.items():
            templates_to_res_ids.setdefault(template, []).append(res_id)
        
        template_id = self.env.ref('nomina_cfdi.email_template_payroll')
        for template, template_res_ids in templates_to_res_ids.items():
            if template.id  == template_id.id:
                for res_id in template_res_ids:
                    payment = self.env[template.model].browse(res_id)
                    if payment.xml_nomina_link:
                        attachments =  results[res_id]['attachments'] or []
                        names = payment.xml_nomina_link.split('/')
                        fn = names[len(names) - 1]
                        data = open(payment.xml_nomina_link, 'rb').read()
                        attachments.append((fn, base64.b64encode(data)))
                        results[res_id]['attachments'] = attachments
        return results
 """
