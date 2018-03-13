# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Impuestos(models.Model):
    _name = 'catalogos.impuestos'
    _rec_name = "descripcion"

    c_impuesto = fields.Char(string='c_Impuesto')
    descripcion = fields.Char(string='Descripción')
    retencion = fields.Char(string='Retención')
    traslado = fields.Char(string='Traslado')
    local_o_federal = fields.Char(string='Local o federal')
    entidad_en_quien_se_aplica = fields.Char(string='Entidad en la que aplica')
