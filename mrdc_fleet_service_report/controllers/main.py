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

import json

from odoo import http
from odoo.http import content_disposition, request, \
    serialize_exception as _serialize_exception
from odoo.tools import html_escape


class MRDCFleetServiceReportController(http.Controller):
    """Controller to generate and print XLS or PDF reports."""

    @http.route('/mrdc_fleet_service_report', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name, method_name='get_xlsx_report'):
        """Function to retrieve an XLS report using a dynamic method name."""
        report_obj = request.env[model].with_user(request.session.uid)
        options = json.loads(options)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                method = getattr(report_obj, method_name, None)
                if not method:
                    return request.make_response(html_escape(json.dumps({
                        'code': 200,
                        'message': 'Odoo Server Error',
                        'data': f'Method {method_name} not found on model {model}'
                    })))
                method(options, response)
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))