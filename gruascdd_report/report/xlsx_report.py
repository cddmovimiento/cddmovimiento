import json
import logging
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from pytz import timezone
import pytz
import math

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')


class projectTaskXlsx(models.AbstractModel):
    _name = 'report.project.task.xlsx'
    _description = 'Reporte de tareas en excel'
    _inherit = 'report.report_xlsx.abstract'

    def float_time_convert(self, float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return (factor * int(math.floor(val)), int(round((val % 1) * 60)))
    
    def generate_xlsx_report(self, workbook, data, obj):
        USD = 2
        MXN = 33
        cantidad = 1
        sheet = workbook.add_worksheet('')
        group = '__export__.res_groups_133_72140141'

        # Formatos
        f_report_header = workbook.add_format({
            'font_size': 14,
            'bottom': True, 'right': True, 'left': True, 'top': True,
            'align': 'center',
            'bold': True
        })
        f_report_date = workbook.add_format({
            'font_size': 10, 'align': 'left',
            'right': False, 'left': False, 'bottom': False, 'top': False,
            'bold': True,
            'text_wrap': True
        })
        f_table_header = workbook.add_format({
            'font_size': 12,
            'bold': True, 'border': 1,
            'valign': 'top', 'align': 'center',
            'text_wrap': 'true'
        })
        f_table_cell_text = workbook.add_format({
            'font_size': 12,
            'align': 'left',
            'text_wrap': 'true'
        })
        f_table_cell_date = workbook.add_format({
            'font_size': 12,
            'align': 'right',
            'num_format': 'dd/mm/yyyy hh:mm AM/PM'
        })
        f_table_cell_money = workbook.add_format({
            'font_size': 12,
            'align': 'right',
            'num_format': '$#,##0.00'
        })
        f_table_cell_number = workbook.add_format({
            'font_size': 12,
            'align': 'right',
        })

        # Encabezado de reporte
        sheet.merge_range('A2:V2', self.env.user.company_id.name, f_report_header)
        sheet.merge_range('A3:V3', 'Resumen de actividades', f_report_header)
        sheet.merge_range('A5:D5',
                          _("Fecha de impresión: " +
                            datetime.today().replace(microsecond=0).strftime('%d-%m-%Y %H:%M:%S')),
                          f_report_date)

        # Encabezadode la tabla
        sheet.set_column('A:C', 15)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:K', 10)
        
        sheet.set_column('L:N', 50)
        sheet.set_column('O:P', 25)
        sheet.set_column('Q:Q', 15)
        sheet.set_column('R:R', 30)
        sheet.set_column('S:S', 15)
        sheet.set_column('T:AB', 25)
        sheet.set_column('AC:AD', 15)
        sheet.set_column('AE:AE', 40)
        sheet.set_column('AF:AF', 16)
        sheet.set_column('AG:AG', 40)
        sheet.set_column('AH:AH', 16)
        sheet.set_column('AI:AI', 40)
        sheet.set_column('AJ:AJ', 16)
        sheet.set_column('AK:AK', 40)

        y_title = 6  # 8
        sheet.write(y_title, 0, 'Trabajo #', f_table_header) #A
        sheet.write(y_title, 1, 'Folio #', f_table_header) #B
        sheet.write(y_title, 2, 'Número de contrato (GSM)', f_table_header) #C
        
        sheet.write(y_title, 3, 'Grúa # ', f_table_header) #D
        
        sheet.write(y_title, 4, 'Odómetro Ini ', f_table_header) #E
        sheet.write(y_title, 5, 'Odómetro Fin ', f_table_header) #F
        sheet.write(y_title, 6, 'Odómetro Delta ', f_table_header) #G
        sheet.write(y_title, 7, 'Horómetro Ini ', f_table_header) #H
        sheet.write(y_title, 8, 'Horómetro Fin ', f_table_header) #I
        sheet.write(y_title, 9, 'Horómetro Delta ', f_table_header) #J
        sheet.write(y_title, 10, 'Diesel ', f_table_header) #K
        
        sheet.write(y_title, 11, 'Nombre tarea', f_table_header) #L
        sheet.write(y_title, 12, 'Cliente', f_table_header) #M
        sheet.write(y_title, 13, 'Locación', f_table_header) #N

        sheet.write(y_title, 14, 'Inicio', f_table_header) #O
        sheet.write(y_title, 15, 'Final', f_table_header) #P

        sheet.write(y_title, 16, 'Total Horas', f_table_header) #Q

        sheet.write(y_title, 17, 'Detalle ', f_table_header) #R

        sheet.write(y_title, 18, 'Cantidad de Grúas', f_table_header) #S

        if self.env.user.has_group (group):
            sheet.write(y_title, 19, 'Precio MXN', f_table_header) #T
            sheet.write(y_title, 20, 'Sub Total MXN', f_table_header) #U
            sheet.write(y_title, 21, 'IVA MXN', f_table_header) #V
            sheet.write(y_title, 22, 'Total MXN', f_table_header) #W
            sheet.write(y_title, 23, 'Precio USD', f_table_header) #X
            sheet.write(y_title, 24, 'Sub Total USD', f_table_header) #Y
            sheet.write(y_title, 25, 'IVA USD', f_table_header) #Z
            sheet.write(y_title, 26, 'Total USD', f_table_header) #AA 
            sheet.write(y_title, 27, 'Pagado MXN', f_table_header) #AB
            sheet.write(y_title, 28, 'Estatus de cotización', f_table_header) #AC
            sheet.write(y_title, 29, 'Estatus operativo', f_table_header) #AD
            sheet.write(y_title, 30, 'Operador de Grúa', f_table_header) #AE
            sheet.write(y_title, 31, 'Horas Generadas Operador', f_table_header) #AF
            sheet.write(y_title, 32, 'Ayudante de Grúa', f_table_header) #AG
            sheet.write(y_title, 33, 'Horas Generadas Ayudante', f_table_header) #AH
            sheet.write(y_title, 34, 'Tercer Ayudante de Grúa', f_table_header) #AI
            sheet.write(y_title, 35, 'Horas Generadas Tercer Ayudante', f_table_header) #AJ
            sheet.write(y_title, 36, 'Comentarios', f_table_header) #AJ
        else:
            sheet.write(y_title, 19, 'Estatus de cotización', f_table_header) #AC
            sheet.write(y_title, 20, 'Estatus operativo', f_table_header) #AD
            sheet.write(y_title, 21, 'Operador de Grúa', f_table_header) #AE
            sheet.write(y_title, 22, 'Horas Generadas Operador', f_table_header) #AF
            sheet.write(y_title, 23, 'Ayudante de Grúa', f_table_header) #AG
            sheet.write(y_title, 24, 'Horas Generadas Ayudante', f_table_header) #AH
            sheet.write(y_title, 25, 'Tercer Ayudante de Grúa', f_table_header) #AI
            sheet.write(y_title, 26, 'Horas Generadas Tercer Ayudante', f_table_header) #AJ
            sheet.write(y_title, 27, 'Comentarios', f_table_header) #AJ

        # Obtener los registros
        if data:
            options = json.loads(data['options'])
            if options['date_filtered_init']:
                options['date_filtered_init'] = datetime.strptime(options['date_filtered_init'], '%Y-%m-%d %H:%M:%S')
            if options['date_filtered_end']:
                options['date_filtered_end'] = datetime.strptime(options['date_filtered_end'], '%Y-%m-%d %H:%M:%S')

            if options['type_filtered'] == 'state':
                objs = self.env['sale.order'].search([
                    '&', ('active_task', '=', True), ('state', '=', options['state'])
                ])
            elif options['type_filtered'] == 'uni_eco':
                _logger.info("Unidad: %s", options['vehicle_id'])
                objs = self.env['sale.order'].search([
                    '&', ('active_task', '=', True), ('vehicle_id', '=', options['vehicle_id'])
                ])
            elif options['type_filtered'] == 'date_create':
                objs = self.env['sale.order'].search([
                    '&', '&', ('active_task', '=', True),
                    ('date_order', '>', options['date_filtered_init']),
                    ('date_order', '<', options['date_filtered_end'])
                ])
            elif options['type_filtered'] == 'date_ejec':
                objs = self.env['sale.order'].search([
                    '&', '&', ('active_task', '=', True),
                    ('task_date_last_stage_update', '>', options['date_filtered_init']),
                    ('task_date_last_stage_update', '<', options['date_filtered_end'])
                ])
            elif options['type_filtered'] == 'all':
                objs = self.env['sale.order'].search([
                    ('active_task', '=', True)
                ])

        y_title += 1

        # Llenando latabla
        for rec in objs.sorted(lambda x: x.name, reverse=True):
            horas = 0
            products = []

            if rec.tasks_ids:
                # _logger.info("#####################Orden: %s", rec.name)
                for binnacle in rec.tasks_ids[0].binnacle_ids:
                    # _logger.info("Biacle %s, %s, %f", binacle.gruero_id.mapped('name'), binacle.support_id.mapped('name'), binacle.delta)
                    horas += binnacle.delta

                    products.append(binnacle.product_id.id)

            unique_products = (list(set(products)))

            payment_state = 'Sin Facturar'

            if rec.invoice_ids:
                if rec.invoice_ids[0].payment_state == 'not_paid':
                    payment_state = 'Sin pagar'
                elif rec.invoice_ids[0].payment_state == 'in_payment':
                    payment_state = 'En Proceso de Pago'
                elif rec.invoice_ids[0].payment_state == 'paid':
                    payment_state = 'Pagado'
                elif rec.invoice_ids[0].payment_state == 'partial':
                    payment_state = 'Pagado Parcialmente'
                elif rec.invoice_ids[0].payment_state == 'reversed':
                    payment_state = 'Revertido'
                elif rec.invoice_ids[0].payment_state == 'invoicing_legacy':
                    payment_state = 'Sistema anterior de facturacion'
                # ayudantes = rec.tasks_ids[0].user_ids.filtered(lambda x : x.type_employee == 'support').mapped('name')

            if rec.tasks_ids:
                tz = self.env.user.tz or self.env._context.get('tz') # Find Timezone from user or partner or employee
                att_tz = timezone(tz or 'utc') 
                
                for task in rec.tasks_ids[0]:

                    for product in task.binnacle_ids:

                        tz = self.env.user.tz or self.env._context.get('tz') # Find Timezone from user or partner or employee
                        att_tz = timezone(tz or 'utc') # If no tz then return in UTC
                        attendance_dt = datetime.strptime(str(product.date_init), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
                        att_tz_dt = pytz.utc.localize(attendance_dt)
                        local_date_init = att_tz_dt.astimezone(att_tz) 

                        tz = self.env.user.tz or self.env._context.get('tz') # Find Timezone from user or partner or employee
                        att_tz = timezone(tz or 'utc') # If no tz then return in UTC
                        attendance_dt = datetime.strptime(str(product.date_end), DEFAULT_SERVER_DATETIME_FORMAT) #Input date
                        att_tz_dt = pytz.utc.localize(attendance_dt)
                        local_date_end = att_tz_dt.astimezone(att_tz) 

                        hour, minute = self.float_time_convert(product.hourmeter_init)
                        hourmeter_init = '{0:02d}:{1:02d}'.format(hour, minute)

                        hour, minute = self.float_time_convert(product.hourmeter_end)
                        hourmeter_end = '{0:02d}:{1:02d}'.format(hour, minute)

                        hour, minute = self.float_time_convert(product.delta_hourmeter)
                        delta_hourmeter = '{0:02d}:{1:02d}'.format(hour, minute)
                        
                        product_name = rec.tasks_ids[0].binnacle_ids.filtered(
                            lambda u: u.product_id.id == product.product_id.id)
                        order_line = rec.order_line.filtered(lambda u: u.product_id.id == product.product_id.id)

                        if order_line[0].product_uom_qty == 0:
                            cantidad = 1
                        else:
                            cantidad = order_line[0].product_uom_qty

                        product_price_subtotal = sum(
                            rec.order_line.filtered(lambda u: u.product_id.id == product.product_id.id).mapped(
                                'price_subtotal')) / cantidad
                        product_price_iva = sum(
                            rec.order_line.filtered(lambda u: u.product_id.id == product.product_id.id).mapped(
                                'price_tax')) / cantidad

                        sheet.write(y_title, 0, rec.name, f_table_cell_text)
                        sheet.write(y_title, 1, product.folio if product.folio else '', f_table_cell_text)
                        sheet.write(y_title, 2, rec.tasks_ids[0].x_studio_contrato if rec.tasks_ids[0].x_studio_contrato else ' ',f_table_cell_text)
                        sheet.write(y_title, 3, product.vehicle_id.x_studio_numero_economico if product else '', f_table_cell_text)
                        
                        sheet.write(y_title, 4, product.odometer_init if product.odometer_init else 0.00, f_table_cell_number)
                        sheet.write(y_title, 5, product.odometer_end if product.odometer_end else 0.00, f_table_cell_number)
                        sheet.write(y_title, 6, product.delta_odometer if product.delta_odometer else 0.00, f_table_cell_number)

                        sheet.write(y_title, 7, hourmeter_init if product.hourmeter_init else "0:00", f_table_cell_text)
                        sheet.write(y_title, 8, hourmeter_end if product.hourmeter_end else "0:00", f_table_cell_text)
                        sheet.write(y_title, 9, delta_hourmeter if product.delta_hourmeter else "0:00", f_table_cell_text)

                        sheet.write(y_title, 10, product.gasolina if product.gasolina else 0.00, f_table_cell_number)

                        sheet.write(y_title, 11, rec.tasks_ids[0].name if rec.tasks_ids else '', f_table_cell_text)
                        sheet.write(y_title, 12, rec.partner_id.name, f_table_cell_text)
                        sheet.write(y_title, 13, rec.pozo, f_table_cell_text)
                        sheet.write(y_title, 14, local_date_init.strftime('%d-%m-%Y %H:%M:%S'), f_table_cell_date)
                        sheet.write(y_title, 15, local_date_end.strftime('%d-%m-%Y %H:%M:%S'), f_table_cell_date)
                        sheet.write(y_title, 16, product.delta, f_table_cell_number)
                        sheet.write(y_title, 17, product.product_id.name if product_name else ' ', f_table_cell_text)
                        sheet.write(y_title, 18, 1, f_table_cell_number)

                        if self.env.user.has_group (group):
                            if order_line[0].currency_id.id == MXN:
                                sheet.write(y_title, 19, order_line[0].price_unit if order_line else '', f_table_cell_money)
                                sheet.write(y_title, 20, product_price_subtotal, f_table_cell_money)
                                sheet.write(y_title, 21, product_price_iva, f_table_cell_money)
                                sheet.write(y_title, 22, (product_price_subtotal + product_price_iva), f_table_cell_money)
                                sheet.write(y_title, 23, 0.00, f_table_cell_money)
                                sheet.write(y_title, 24, 0.00, f_table_cell_money)
                                sheet.write(y_title, 25, 0.00, f_table_cell_money)
                                sheet.write(y_title, 26, 0.00, f_table_cell_money)
                            elif order_line[0].currency_id.id == USD:
                                sheet.write(y_title, 19, 0.00, f_table_cell_money)
                                sheet.write(y_title, 20, 0.00, f_table_cell_money)
                                sheet.write(y_title, 21, 0.00, f_table_cell_money)
                                sheet.write(y_title, 22, 0.00, f_table_cell_money)
                                sheet.write(y_title, 23, order_line[0].price_unit if order_line else '', f_table_cell_money)
                                sheet.write(y_title, 24, product_price_subtotal, f_table_cell_money)
                                sheet.write(y_title, 25, product_price_iva, f_table_cell_money)
                                sheet.write(y_title, 26, (product_price_subtotal + product_price_iva), f_table_cell_money)

                            sheet.write(y_title, 27, rec.get_paid_ammount(), f_table_cell_money)
                            sheet.write(y_title, 28, payment_state, f_table_cell_text)
                            sheet.write(y_title, 29, rec.tasks_ids[0].stage_id.name, f_table_cell_text)
                            sheet.write(y_title, 30, product.gruero_id.name if product.gruero_id else ' ',f_table_cell_text)
                            sheet.write(y_title, 31, product.delta if product.gruero_id else 0.00, f_table_cell_number)
                            sheet.write(y_title, 32, product.ayudante_id.name if product.ayudante_id else ' ',f_table_cell_text)
                            sheet.write(y_title, 33, product.delta if product.ayudante_id else 0.00, f_table_cell_number)
                            sheet.write(y_title, 34, product.tercer_ayudante_id.name if product.tercer_ayudante_id else ' ',f_table_cell_text)
                            sheet.write(y_title, 35, product.delta if product.tercer_ayudante_id else 0.00,f_table_cell_number)
                            sheet.write(y_title, 36, product.comment if product.comment else ' ',f_table_cell_text)
                        else:
                            sheet.write(y_title, 19, payment_state, f_table_cell_text)
                            sheet.write(y_title, 20, rec.tasks_ids[0].stage_id.name, f_table_cell_text)
                            sheet.write(y_title, 21, product.gruero_id.name if product.gruero_id else ' ',f_table_cell_text)
                            sheet.write(y_title, 22, product.delta if product.gruero_id else 0.00, f_table_cell_number)
                            sheet.write(y_title, 23, product.ayudante_id.name if product.ayudante_id else ' ',f_table_cell_text)
                            sheet.write(y_title, 24, product.delta if product.ayudante_id else 0.00, f_table_cell_number)
                            sheet.write(y_title, 25, product.tercer_ayudante_id.name if product.tercer_ayudante_id else ' ',f_table_cell_text)
                            sheet.write(y_title, 26, product.delta if product.tercer_ayudante_id else 0.00,f_table_cell_number)
                            sheet.write(y_title, 27, product.comment if product.comment else ' ',f_table_cell_text)

                        y_title += 1
