# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TipoRelacion(models.Model):
    _name = 'catalogos.tipo_relacion'
    _rec_name = "descripcion"

    c_tipo_relacion = fields.Char(string='c_TipoRelacion')
    descripcion = fields.Char(string='Descripción')
    fecha_inicio_vigencia = fields.Date(string='Fecha inicio de vigencia')
    fecha_fin_vigencia = fields.Date(string='Fecha fin de vigencial')