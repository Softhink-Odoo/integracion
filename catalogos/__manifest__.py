# -*- coding: utf-8 -*-
{
    'name': "catalogos",

    'summary': """
        Contiene los Catalogos requeridos por el SAT para la facturación en 3.3""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Softhink",
    'website': "http://www.sft.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views_c_aduanas.xml',
        'Archivos_CSV/catalogos.aduanas.csv',
        'views/views_c_ClaveProdServicios.xml',
        'Archivos_CSV/catalogos.clave_prod_serv.csv',
        'views/views_c_ClaveUnidad.xml',
        'Archivos_CSV/catalogos.clave_unidad.csv',
        'views/views_Codigo_P.xml',
        'Archivos_CSV/catalogos.codigo_postal.csv',
        'views/views_forma_de_pago.xml',
        'Archivos_CSV/catalogos.forma_pago.csv',
        'views/views_metodo_pago.xml',
        'Archivos_CSV/catalogos.metodo_pago.csv',
        'views/views_impuestos.xml',
        'Archivos_CSV/catalogos.impuestos.csv',
        'views/views_NumPedimentoAduana.xml',
        'Archivos_CSV/catalogos.num_pedimento_aduana.csv',
        'views/views_c_paises.xml',
        'Archivos_CSV/catalogos.paises.csv',
        'views/views_c_patente_aduanal.xml',
        'Archivos_CSV/catalogos.patente_aduanal.csv',
        'views/views_c_regimen_fiscal.xml',
        'Archivos_CSV/account.fiscal.position.csv',
        'views/views_c_tasa_cuota.xml',
        'Archivos_CSV/catalogos.tasa_cuota.csv',
        'views/views_c_tipo_factor.xml',
        'Archivos_CSV/catalogos.tipo_factor.csv',
        'views/views_c_tipo_relacion.xml',
        'Archivos_CSV/catalogos.tipo_relacion.csv',
        'views/views_c_uso_cfdi.xml',
        'Archivos_CSV/catalogos.uso_cfdi.csv',
        'views/views_c_tipo_comprobante.xml',
        'Archivos_CSV/catalogos.tipo_comprobante.csv',
        'views/views_c_configuracion.xml',
        'Archivos_CSV/catalogos.configuracion.csv',
        'views/views_bancos.xml',
        #Asigna los catalogos a los impuestos por defecto
        
    ],
    # only loaded in demonstration mode
    'demo': [
         
    ],
}
