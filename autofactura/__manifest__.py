# -*- coding: utf-8 -*-
{
    'name': "SFT-Autofactura",

    'summary': """
        Sft-Facturación | Complemento de autofactura""",

    'description': """
        Complemento del módulo de facturación electrónica para que tus clientes generen la factura desde tu portal web, a través del pedido de venta.
    """,

    'author': "Softhink",
    'website': "http://www.sft.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website','catalogos','sft-facturacion'],

    # always loaded
    'data': [
        'templates/tamplate.xml',
    ],
    'qweb': ['static/src/xml/pos_ticket_view.xml'],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
        #"autofactura/template.xml"
    ],
    "images":['static/description/Integracion4.jpg']
}
