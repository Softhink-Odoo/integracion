# -*- coding: utf-8 -*-

from odoo import http
#from autofactura.controllers.autofactura_utils import AutofacturaUtils
#from autofactura_utils import AutofacturaUtils


class AutofacturaWS(http.Controller):
    @http.route('/autofactura_ws/pedido', type='json', auth='public', methods=['POST'], website=True)
    def ws_pedido(self, **kw):
        pedido_nombre = kw['name'];
        #fecha_pedido = kw['fecha_pedido'];
        importe = kw['importe'];
        rfc_compania = kw['compania_cmb'];
        # pedido = self.utils.buscaPedido(pedido_nombre, importe, rfc_compania, None);
        #
        # retorno_pedido = {};
        # retorno_pedido["name"] = pedido.name;
        # retorno_pedido["compania"] = pedido.company_id.name;
        # retorno_pedido["rfc_compania"] = pedido.company_id.company_registry;
        # retorno_pedido["importe"] = pedido.amount_total;
        # retorno_pedido["cliente_rfc"] = pedido.partner_id.rfc_cliente;
        # retorno_pedido["cliente_mail"] = pedido.partner_id.email;
        # #retorno_pedido["importe"] = pedido.amount_total;
        #
        # return [{'status': 'test',
        #          'pedido': retorno_pedido,
        #          }]
