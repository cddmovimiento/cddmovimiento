# -*- coding: utf-8 -*-
{
    'name': "Personalización de compra",
    'version' : "1.0",

    'summary': """
        Personalizaciones al módulo de compras odoo""",

    'description': """
        Agrega funcionalidad para aprobar múltiples compras a la vez.
    """,

    'author': "Javier Pineda Rodriguez",
    'website': "http://www.skillsdepot.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'purchase',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase'],


    # always loaded
    'data': [
        'views/actions.xml',
    ],
    'assets': {
    },
    # only loaded in demonstration mode
    'demo': [
    ],
    'qweb':[
    ],
    'application': False,
    'sequence': 1
}
