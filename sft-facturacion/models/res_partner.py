# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo import models, fields, api
import re

#Agrega el campo RFC al formulario de Clientes y Proveedores
class RFCClientes(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    is_a_user = fields.Boolean(string='Es un usuario?',default=False)
    rfc_cliente = fields.Char(string='RFC',size=13)
    colonia = fields.Char(string='Colonia')
    numero_int = fields.Char(string='Numero Int')
    numero_ext = fields.Char(string='Numero Exterior')
    nif = fields.Char(string='NIF EXTRA')
    cfdi = fields.Boolean(string='Activar CFDI')
    municipio = fields.Char(string='Municipio')
    company_type = fields.Selection([
            ('person','Persona Fisica'),
            ('company', 'Persona Moral'),
        ], index=True, default='person',
        track_visibility='onchange', copy=False)
    #Los Siguientes campos son relacionales extra que solo si estan configurados
    #Se cargan en la Factura de Venta al Seleccionar el cliente.
    #Por tanto no son obligatorios.
    metodo_pago_id = fields.Many2one('catalogos.metodo_pago', string='Metodo de pago')
    uso_cfdi_id = fields.Many2one('catalogos.uso_cfdi', string='Uso CFDI')


    partner_notifica_ids = fields.One2many('res.partner.notifica', 'partner_id', string='Notificaciones', copy=False)

    @api.onchange('rfc_cliente')
    def set_upper(self):
        for record in self:
            if record.rfc_cliente != None:
                record.rfc_cliente = str(record.rfc_cliente).upper()


    @api.constrains('rfc_cliente','country_id')
    def validar_RFC(self):
        for record in self:
            if record.customer== True:
                if record.cfdi == True:
                    if record.rfc_cliente == False:
                        if record.nif == False:
                            raise ValidationError("Error de Validacion : El cliente %s no tiene ningun RFC asignado, favor de asignarlo primero" % (record.name))
                    else:
                        if record.is_company == True:
                            #Valida RFC en base al patron de una persona Moral
                            if len(record.rfc_cliente)!=12:
                                raise ValidationError("El RFC %s no tiene la logitud de 12 caracteres para personas Morales que establece el sat" % (record.rfc_cliente))
                            else:
                                patron_rfc = re.compile(r'^([A-ZÑ\x26]{3}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))((-)?([A-Z\d]{3}))?$')
                                if not patron_rfc.search(record.rfc_cliente.upper()):
                                    msg = "Formato RFC de Persona Moral Incorrecto"
                                    raise ValidationError(msg)
                        else:
                            #Valida el RFC en base al patron de una Persona Fisica
                            if len(record.rfc_cliente)!=13:
                                raise ValidationError("El RFC %s no tiene la logitud de 13 caracteres para personas Fisicas que establece el sat" % (record.rfc_cliente))
                            else:
                                patron_rfc = re.compile(r'^([A-ZÑ\x26]{4}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))((-)?([A-Z\d]{3}))?$')
                                if not patron_rfc.search(record.rfc_cliente.upper()):
                                    msg = "Formato RFC de Persona Fisica Incorrecto"
                                    raise ValidationError(msg)

    @api.constrains('nif')
    def validar_NIF(self):
        for record in self:
            if record.customer== True:
                if record.cfdi == True:
                    if record.nif == False:
                        if record.rfc_cliente == False:
                            raise ValidationError("Error de Validacion : El cliente de origen extranjero %s no tiene el NIF registrado, favor de asignarlo primero" % (record.name))

    @api.constrains('email')
    def validar_Email(self):
        for record in self:
            if record.customer== True:
                if record.cfdi == True:
                    if record.email == False:
                            raise ValidationError("Error de Validacion : El cliente %s no tiene asignado ningun Correo Electronico, favor de asignarlo primera" % (record.name))

    @api.constrains('zip')
    def validar_Codigo_Postal(self):
        for record in self:
            if record.customer== True:
                if record.cfdi == True:
                    if record.zip == False:
                            raise ValidationError("Error de Validacion : El cliente %s no tiene asignada ningun Codigo Postal, favor de asignarlo primera" % (record.name))

class NotificaCFDI(models.Model):
    _name = 'res.partner.notifica'

    correo = fields.Char(string='Correo', required=True)
    #partner_id = fields.Many2one('account.invoice', string='Invoice Reference',
    #    ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner', string='Cliente Ref', ondelete='cascade')

    # @api.constrains('correo')
    # def correo_validacion(self):
    #     """ make sure nid starts with capital letter, followed by 12 numbers and ends with a capital letter"""
    #     for rec in self:
    #         if not re.match(r"^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$]$", rec.correo):
    #             raise ValidationError("Error de Validacion : El correo (%s) no tiene el formato adecuado" % (rec.correo))
