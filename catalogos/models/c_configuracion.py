# -*- coding: utf-8 -*-
import json
import requests
import hashlib
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo import models, fields, api

class Configuracion(models.Model):
    _name = 'catalogos.configuracion'
    _description = u"Configuracion del usuario y contraseña para el timbrado de la factura"
    _rec_name = "usuario"

    url = fields.Char(string='URL', required=True,)
    usuario = fields.Char(string='Usuario', required=True,)
    contrasena = fields.Char(string='Contraseña', required=True)
    state = fields.Selection([
            ('validar','No Confirmado'),
            ('validado', 'Validado'),
        ], string='Status', index=True, readonly=True, default='validar',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' status is used when the invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.", color="green")

    @api.multi
    def validar_usuario(self):

        service = str(self.url)+"webresources/UsuarioWS/ValidarUsuarioOdoo"
        string=str(self.contrasena.encode("utf-8"))
        #crea el algoritmo para encriptar la informacion
    	algorithim=hashlib.md5()
        #encripta la informacion
    	algorithim.update(string)
        #La decodifica en formato hexadecimal
    	encrypted=algorithim.hexdigest()

        data = {
        "user_odoo":self.usuario,"odoo_contrasena":encrypted,"odoo_pfl_id":"4"
        }



        headers = {
           'content-type': "application/json"
    }
        

        response = requests.request("POST", service, data=json.dumps(data), headers=headers)
        json_data = json.loads(response.text)
            #Valida que la factura haya sido timbrada Correctamente
        if json_data['result']['success']== 'true':
            self.state = 'validado'
           # tkinter.messagebox.showinfo('Resultado','Usuario Valido')
            #raise ValidationError("Texto Encriptado %s Encriptacion %s" %(string,encrypted))
        else:
            raise ValidationError(json_data['result']['message'])

    @api.multi
    def volver_a_validar_usuario(self):
        self.state = 'validar'

    @api.onchange('usuario')
    def _onchange_sin_validar_usuario(self):
        self.state = 'validar'
