# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ClaveUnidad(models.Model):
    _name = 'catalogos.clave_unidad'
    _rec_name = 'nombre'
    _description =u'Catálogo de unidades de medida para los conceptos en el CFDI. Version 2.0'

    c_claveunidad = fields.Char(string="c_ClaveUnidad", required=True)	
    nombre = fields.Char()
    descripcion = fields.Char()
    nota = fields.Text()
    fecha_de_inicio_de_vigencia = fields.Date(string='Inicio de Vigencia')	
    fecha_de_fin_de_vigencia = fields.Date(string='Fin de Vigencia')
    simbolo = fields.Char()

    