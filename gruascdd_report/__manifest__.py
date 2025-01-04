# -*- coding: utf-8 -*-
{
    "name": "Módulo personalizado para CDD",
    "summary": "Modulo que automatiza multiples lineas de una orden de venta, en una sola tarea y un solo proyecto.",
    "author": "Eligio Chan",
    "website": "https://ezzquad.com",
    "category": "Sale",
    "version": "2.0.1",
    "license": "OPL-1",

    # any module necessary for this one to work correctly
    "depends": ["base","project","sale","sale_project","hr","hr_timesheet", "industry_fsm","fleet"],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "report/sale_order_report.xml",
        "wizard/dayli_operations_report.xml",     
        "views/project_task.xml",
    ],
    # only loaded in demonstration mode
    "demo": [

    ],
}


