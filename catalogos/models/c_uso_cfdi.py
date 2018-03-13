# -*- coding: utf-8 -*-

from odoo import models, fields, api

class UsoCFDI(models.Model):
    _name = 'catalogos.uso_cfdi'
    _rec_name = "descripcion"

    c_uso_cfdi = fields.Char(string='c_UsoCFDI')	
    descripcion = fields.Char(string='Descripción')
    fisica = fields.Char(string='Física')
    moral = fields.Char(string='Moral')
    fecha_inicio_vigencia = fields.Date(string='Fecha inicio de vigencia')
    fecha_fin_vigencia = fields.Date(string='Fecha fin de vigencia')