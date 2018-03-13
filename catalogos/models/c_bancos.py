# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Aduanas(models.Model):
    _name = 'catalogos.bancos'
    _description = u"Catálogo de aduanas (tomado del anexo 22, apéndice I de la RGCE 2015)."
    _rec_name = "c_nombre"

    c_nombre = fields.Char(string='Nombre del Banco', required=True)
    rfc_banco = fields.Char(string='RFC Institucion Bancaria')
    clave_institucion_financiera = fields.Char(string='Clave Institucion Financiera')
    