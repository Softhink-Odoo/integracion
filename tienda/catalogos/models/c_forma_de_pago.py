# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FormaPago(models.Model):
    _name = 'catalogos.forma_pago'
    _description = u"Catálogo de formas de pago."
    _rec_name = "descripcion"

    c_forma_pago = fields.Char(string='c_FormaPago')
    descripcion = fields.Char(string='Descripción')
    bancarizado = fields.Char(string='Bancarizado')
    num_op = fields.Char(string='Número de operación')
    rfc_emisor = fields.Char(string='RFC del Emisor de la cuenta ordenante')
    cuenta_ordenante = fields.Char(string='Cuenta Ordenante')	
    patron_cta_ordenante = fields.Char(string='Patrón para cuenta ordenante')	
    rfc_emisor_cta_benef = fields.Char(string='RFC del Emisor/Cuenta de Beneficiario')	
    cta_benenf = fields.Char(string='Cuenta del Benenficiario')
    patron_cta_benef = fields.Char(string='Patrón para la cuenta Beneficiaria')	
    tipo_cad_pago = fields.Char(string='Tipo Cadena Pago')	
    nom_banco_emisor_cta_ord_ext = fields.Char(string='Nombre del Banco emisor de la cuenta ordenante en caso de extranjero')	
    fecha_inicio_de_vigencia = fields.Date(string='Fecha inicio de vigencia')	
    fecha_fin_de_vigencia = fields.Date(string='Fecha fin de vigencia')
    