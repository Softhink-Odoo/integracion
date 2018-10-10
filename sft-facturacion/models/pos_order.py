# -*- coding: utf-8 -*-
import re
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo import api, fields, models

class PosOrder(models.Model):
    _name = 'pos.order'
    _inherit = 'pos.order'

    @api.multi
    def action_pos_order_invoice(self):
        print "action_pos_order_invoice"
        codigo_search = self.env['catalogos.codigo_postal'].search([('c_codigopostal', '=',self.env.user.company_id.zip)])
        if codigo_search.id== False:
            raise ValidationError("Compruebe el Codigo Postal colocado en la configuracion de la compania ya que no se encuentra en el catalogo del sat")

        if self.env.user.company_id.state_id.name == False:
            raise ValidationError("La Compañia no tiene asignado ningun Estado")

        referencia = self.name;


        res = super(PosOrder,self).action_pos_order_invoice();
        invoice = self.env['account.invoice'].browse(res['res_id'])

        valores = {"metodo_pago_id" : self.partner_id.metodo_pago_id.id,
            "uso_cfdi_id" : self.partner_id.uso_cfdi_id.id,
            'compania_estado': self.env.user.company_id.state_id.name,
            'rfc_cliente_factura': (self.partner_id.rfc_cliente).encode('utf-8'),
            'rfc_emisor': (self.env.user.company_id.company_registry).encode('utf-8'),
            'compania_calle': (self.env.user.company_id.street).encode('utf-8'),
            'compania_ciudad': (self.env.user.company_id.city).encode('utf-8'),
            'compania_pais': (self.env.user.company_id.country_id.name).encode('utf-8'),
            'observaciones' : ("REFERENCIA: "+referencia).encode('utf-8')
        }

        invoice.write(valores)

        return res;
