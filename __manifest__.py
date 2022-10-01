# -*- coding: utf-8 -*-
{
    'name': "method_supermercado_social",

    'summary': """
        Módulo para la localización del Supermercado Soial""",

    'description': """
        Prepara los datos en la ficha del beneficiario:
        Nombre completo
        El día de retiro
        La hora de retiro 
        Si esta la día con la menbresia
        El tamañp del grupo familiar
    """,

    'author': "Method ERP",
    'website': "http://www.Method ERP",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/pagos.xml',
        'views/facturas.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
        'static/src/xml/templates.xml',
    ],
    'qweb': [
        'static/src/xml/partner.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}