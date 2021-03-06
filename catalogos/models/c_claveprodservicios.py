# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ClaveProdServicios(models.Model):
    _name = 'catalogos.clave_prod_serv'
    _description=u"Catálogo de productos / servicios."
    _rec_name = 'descripcion'

    c_claveprodserv = fields.Text(string='c_CaveProdServ')
    descripcion = fields.Char(string='Descripcion')
    fechainiciovigencia = fields.Date(string='Inicio de Vigencia')
    fechafinvigencia = fields.Date(string='Fin de la Vigencia')	
    incluir_iva_trasladado = fields.Char(string='Incluir IVA Traslado')	
    incluir_ieps_trasladado = fields.Char(string='Incluir IEPS Trasladado')
    complemento_que_debe_incluir = fields.Char(string='Complemento que debe incluir')
    palabras_similares = fields.Char(string='Palabras Similares')

    
