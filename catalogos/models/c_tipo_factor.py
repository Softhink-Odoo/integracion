# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TipoFactor(models.Model):
    _name = 'catalogos.tipo_factor'
    _rec_name = "tipo_factor"

    tipo_factor = fields.Char(string='Tipo de Factor') 