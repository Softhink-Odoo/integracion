# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MetodoPago(models.Model):
    _name = 'catalogos.metodo_pago'
    _rec_name = "descripcion"

    c_metodo_pago = fields.Char("c Metodo Pago")	
    descripcion = fields.Char("Descripcion")	
    fecha_inicio_vigencia = fields.Date(string='Fecha de inicio de Vigencia')
    fecha_fin_vigencia = fields.Date(string='Fecha de Fin de Vigencia')
