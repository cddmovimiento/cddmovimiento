# -*- coding: utf-8 -*-
{
    "name": "Módulo personalizado para CDD",
    "summary": "Modulo que automatiza multiples lineas de una orden de venta, en una sola tarea y un solo proyecto.",
    "author": "Eligio Chan",
    "website": "https://ezzquad.com",
    "category": "Sale",
    "version": "2.0",
    "license": "OPL-1",

    # any module necessary for this one to work correctly
    "depends": ["base","project","sale","sale_project","hr","hr_timesheet", "industry_fsm","fleet"],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/project_task.xml",
        "views/sale_order.xml",
        "views/hr_employee.xml",
        "views/fleet_vehicle.xml",
        "views/fleet_vehicle_hourmeter.xml",
    ],
    # only loaded in demonstration mode
    "demo": [

    ],
}

