# -*- coding: utf-8 -*-
from odoo import http
from datetime import datetime
import json
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import hashlib

class AutofacturaUtils(http.Controller):
    def buscaPedido(self, name, total, rfc_compania, fecha):
        SaleOrder = http.request.env['sale.order']
        #pedidos = self.env['sale.order'].search([('name', '=', pedido_nombre)])
        print name;
        print fecha;
        print "Compania "+rfc_compania;
        print str(float(total));

        #d1 = datetime.strftime(fecha, "%Y-%m-%d %H:%M:%S")
        #d2 = datetime.strftime(fecha, "%Y-%m-%d 24:59:59")


        #pedidos = SaleOrder.search([('name', '=', pedido_nombre), ('amount_total', '=', float(importe)), ('confirmation_date', '>=', d1), ('confirmation_date', '<=', d2)])
        pedidos = SaleOrder.sudo().search([('name', '=', name), ('amount_total', '=', float(total))])

        for pedido in pedidos:
            if rfc_compania == pedido.company_id.company_registry:
                return pedido;

        return None;

    def buscaPedidoPOS(self, name, total, rfc_compania, fecha):
        PosOrder = http.request.env['pos.order']
        #pedidos = self.env['sale.order'].search([('name', '=', pedido_nombre)])
        print name;
        print fecha;
        print "Compania "+rfc_compania;
        print str(float(total));

        #d1 = datetime.strftime(fecha, "%Y-%m-%d %H:%M:%S")
        #d2 = datetime.strftime(fecha, "%Y-%m-%d 24:59:59")


        #pedidos = SaleOrder.search([('name', '=', pedido_nombre), ('amount_total', '=', float(importe)), ('confirmation_date', '>=', d1), ('confirmation_date', '<=', d2)])
        pedidos = PosOrder.sudo().search([('name', '=', name), ('amount_total', '=', float(total))])

        if len(pedidos) == 0:
            return None;

        #for pedido in pedidos:
        #    if rfc_compania == pedido.company_id.company_registry:
        #        return pedido;

        return pedidos[0];
