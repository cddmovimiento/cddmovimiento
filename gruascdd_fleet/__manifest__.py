# -*- coding: utf-8 -*-
{
    "name": "Módulo personalizado para CDD para la flota",
    "summary": "Modulo que automatiza multiples lineas de una orden de venta, en una sola tarea y un solo proyecto.",
    "author": "Eligio Chan",
    "website": "https://ezzquad.com",
    "category": "Sale",
    "version": "2.0.1",
    "license": "OPL-1",

    # any module necessary for this one to work correctly
    "depends": ["base","fleet", "hr", 'gruascdd'],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "data/secuence.xml",
        "data/email_template.xml",       
        "views/fleet_vehicle.xml",
        "views/fleet_services_config_view.xml",
        "views/fleet_vehicle_log_service_inh.xml",
        "views/fleet_service_type.xml"
    ],
    # only loaded in demonstration mode
    "demo": [

    ],
}

