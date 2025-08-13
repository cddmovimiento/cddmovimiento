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
{
    'name': "MRDC - Fleet Service Report",

    'summary': """
        Odoo module for Fleet Service Report.
        """,

    'description': """
        Odoo module for Fleet Service Report.
        """,

    'author': "Rodrigo Contreras",
    'website': "https://mrdc.tech",
    'category': 'Fleet',
    'version': '1.0.0',

    'depends': ['fleet', 'gruascdd_fleet'],

    'data': [

        'security/ir.model.access.csv',
        'wizard/mrdc_fleet_service_report_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'mrdc_fleet_service_report/static/src/js/action_manager.js',
        ],
    },

    'external_dependencies': {
        'python' : ['setuptools'],
    },

    'demo': [],
    'license': 'OPL-1',
}
