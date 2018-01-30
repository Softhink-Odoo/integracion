# -*- coding: utf-8 -*-

from odoo import models, fields, api

class RegimenFiscal(models.Model):
    _name = 'account.fiscal.position'
    _inherit = "account.fiscal.position"

    c_regimenfiscal = fields.Char(string='c_RegimenFiscal') 	
    #descripcion = fields.Char(string='Descripción')
    fisica = fields.Char(string='Se aplica a persona Física')
    moral = fields.Char(string='Se aplica a Persona Moral')	
    fecha_inicio_vigencia = fields.Date(string='Fecha de inicio de vigencia')	
    fecha_fin_vigencia = fields.Date(string='Fecha de fin de vigencia')