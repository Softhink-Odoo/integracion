# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TasaCuota(models.Model):
    _name = 'catalogos.tasa_cuota'
    _rec_name = "valor_maximo"

    rango_o_fijo = fields.Char(string='Rango o Fijo')
    valor_minimo  = fields.Float(string='Valor mínimo')	
    valor_maximo = fields.Float(string='Valor máximo')
    impuesto = fields.Char(string='Impuesto')
    factor = fields.Char(string='Factor')
    traslado = fields.Char(string='Traslado')
    retencion = fields.Char(string='Retención')
    fecha_inicio_vigencia = fields.Char(string='Fecha inicio de vigencia')
    fecha_fin_vigencia = fields.Char(string='Fecha fin de vigencia')