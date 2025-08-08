# -*- coding: utf-8 -*-
#################################################################################
# Author      : Rodrigo Contreras (<mrdc.tech>)
# Copyright(c): 2025
# All Rights Reserved.
#
# This module is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models, fields
import io
import json
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PrintFleetServiceReport(models.TransientModel):
    _name = 'mrdc.fleet_service.report'
    _description = 'Print Fleet Service Report'

    start_date = fields.Date(string="Fecha Inicial", required=True)
    end_date = fields.Date(string="Fecha Final", required=True)

    def print_xlsx_report(self):
        """Function to retrieve and open an XLS report record."""
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'mrdc.fleet_service.report',
                     'options': json.dumps(self.read()[0],
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Reporte Servicios',
                     'method_name': 'get_service_xlsx_report',
                     },
            'report_type': 'mrdc_fleet_service_report'
        }

    def get_service_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        start_date = data.get('start_date')
        end_date = data.get('end_date')

        records = self.env['fleet.vehicle.log.services'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])

        sheet = workbook.add_worksheet('Reporte Servicios')

        sheet.set_column('A:A', 2)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 19)
        sheet.set_column('H:H', 19)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 19)
        sheet.set_column('L:L', 18)
        sheet.set_column('M:M', 19)
        sheet.set_column('N:N', 14)
        sheet.set_column('O:O', 35)
        sheet.set_column('P:P', 35)
        sheet.set_column('Q:Q', 35)
        sheet.set_column('R:R', 2)

        table_header_format = workbook.add_format({'font_name': 'Arial', 'font_size': 14, 'font_color': 'black', 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'bg_color': '#C0E6F5', 'bold': True, 'valign': 'vcenter', 'text_wrap': True})
        normal_bordered = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1})
        normal_bordered_wrap = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'align': 'center', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'text_wrap': True})
        date_bordered = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'num_format': 'dd/mm/yyyy'})
        datetime_bordered = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'align': 'left', 'right': 1, 'left': 1, 'top': 1, 'bottom': 1, 'num_format': 'dd/mm/yyyy hh:mm'})

        headers = ['GRUA', 'NO. ECO', 'TIPO DE MANTTO', 'TIPO DE SERVICIO', 'FECHA PROG.', 'FECHA HORA INICIAL', 'FECHA HORA FINAL', 'HORAS', 'LOCACIÓN', 'HORÓMETRO', 'ODÓMETRO', 'HORAS DISPONIBLE', 'HORAS MAQUINA', 'RESPONSABLE', 'AYUDANTE', 'DESCRIPCIÓN DEL TRABAJO']

        for col_num, header in enumerate(headers):
            sheet.write(1, col_num+1, header, table_header_format)

        tipo_servicio_dict = dict(records._fields['tipo_servicio'].selection)

        for row_num, record in enumerate(records, start=2):
            sheet.write(row_num, 1, record.vehicle_id.display_name if record.vehicle_id else '', normal_bordered_wrap)
            sheet.write(row_num, 2, record.folio or '', normal_bordered)
            sheet.write(row_num, 3, record.service_type_id.name or '', normal_bordered)

            tipo_servicio_label = tipo_servicio_dict.get(record.tipo_servicio, '')
            sheet.write(row_num, 4, tipo_servicio_label, normal_bordered)

            sheet.write(row_num, 5, record.date or '', date_bordered)
            sheet.write(row_num, 6, record.date_init or '', datetime_bordered)
            sheet.write(row_num, 7, record.date_end or '', datetime_bordered)
            sheet.write(row_num, 8, record.delta or '', normal_bordered)
            sheet.write(row_num, 9, record.ubicacion or '', normal_bordered)
            sheet.write(row_num, 10, record.hourmeter or '', normal_bordered)
            sheet.write(row_num, 11, record.odometer or '', normal_bordered)
            sheet.write(row_num, 12, '', normal_bordered)
            sheet.write(row_num, 13, '', normal_bordered)
            sheet.write(row_num, 14, record.encargado.name or '', normal_bordered_wrap)
            sheet.write(row_num, 15, record.ayudante.name or '', normal_bordered_wrap)
            sheet.write(row_num, 16, record.description or '', normal_bordered_wrap)

        sheet.hide_gridlines(2)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()