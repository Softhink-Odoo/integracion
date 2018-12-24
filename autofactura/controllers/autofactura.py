# -*- coding: utf-8 -*-
from odoo import http, _
from datetime import datetime
import json
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import hashlib
#from autofactura_utils import AutofacturaUtils
#from autofactura.controllers.autofactura_utils import AutofacturaUtils
import traceback
import logging

class Autofactura(http.Controller):
    #utils = AutofacturaUtils();

    _logger = logging.getLogger(__name__)



    @http.route('/autofactura/autofactura', type='http', auth='public', website=True)
    def index(self, **kw):
        SaleOrder = http.request.env['sale.order']
        pedidos = SaleOrder.sudo().search([])

        Compania = http.request.env['res.company']
        companias = Compania.sudo().search([])

        #pedidos = [];
        #pedidos.append(pedido);
        return http.request.render('autofactura.new_web_page', {'teachers': pedidos, 'companias':companias})

    @http.route('/autofactura/busca_pedido', type='http', methods=['POST'], auth="public", website=True, csrf=False)
    def busca_pedido(self, **kw):
        #here in kw you can get the inputted value
        pedido_nombre = kw['name'];
        #fecha_pedido = kw['fecha_pedido'];
        importe = kw['importe'];
        rfc_compania = kw['compania_cmb'];
        pedido_pos = False;
        pedido = self.buscaPedido(pedido_nombre, importe, rfc_compania, None);

        if pedido == None:
            pedido = self.buscaPedidoPOS(pedido_nombre, importe, rfc_compania, None)
            if pedido == None:
                return http.request.render('autofactura.pedido_no_encontrado', {
                    'mensaje':'No se encontró el pedido solicitado'
                })
            orden = pedido.pos_reference;
            orden = orden.replace(_("Order "), "");
            pedido_pos = True;
            pedido.referencia = orden;

        else:
            pedido.referencia = pedido.name;




        inv_obj = http.request.env['account.invoice']
        invoice = None;


        #Si es pedido de venta directa
        if pedido_pos == False:
            if pedido["state"] != 'sale':#Si no está como Pedido de venta
                return http.request.render('autofactura.pedido_no_encontrado', {
                    'mensaje':'El pedido solicitado no se encuentra disponible para facturar.'
                })

            arr_facturas = inv_obj.sudo().search([('origin','=',pedido_nombre)]);
            if len(arr_facturas) >0:
                invoice = arr_facturas[0];


                # return http.request.render('autofactura.pedido_no_encontrado', {
                #     'mensaje':'El pedido solicitado ya cuenta con factura.'
                # })

        #Si es pedido de POS
        if pedido_pos == True:
            if pedido["state"] in ('draft','cancel'):#Si no está como Pedido de venta
                return http.request.render('autofactura.pedido_no_encontrado', {
                    'mensaje':'El pedido solicitado no se encuentra disponible para facturar.'
                })

            if pedido.invoice_id != None and pedido.invoice_id.id != None:
                invoice = pedido.invoice_id;


        #si ya tiene factura la abre
        if invoice != None and invoice.id != None and invoice.id != False:
            factura=str(invoice.fac_id)
            #string=str(contrasena.encode("utf-8"))
            algorithim=hashlib.md5()
            algorithim.update(factura.encode("utf-8"))
            encrypted=algorithim.hexdigest()

            url_parte = http.request.env['catalogos.configuracion'].sudo().search([('url', '!=', '')])

            url_descarga_pdf = url_parte.url+invoice.pdf+encrypted
            url_descarga_xml = url_parte.url+invoice.xml+encrypted



            return http.request.render('autofactura.factura_timbrada', {
                'factura': invoice,
                'url_descarga_pdf':url_descarga_pdf,
                'url_descarga_xml':url_descarga_xml,
            })

        UsoCfdi = http.request.env['catalogos.uso_cfdi']
        arr_uso_cfdi = UsoCfdi.sudo().search([])

        FormaPago = http.request.env['catalogos.forma_pago']
        arr_forma_pago = FormaPago.sudo().search([])


        MetodoPago = http.request.env['catalogos.metodo_pago']
        arr_metodo_pago = MetodoPago.sudo().search([])

        return http.request.render('autofactura.muestra_pedido', {
            'pedido': pedido,
            'usos_cfdi': arr_uso_cfdi,
            'metodos_pago': arr_metodo_pago,
            "formas_pago":arr_forma_pago
        })


    @http.route('/autofactura/pedido', type='json', auth='public', methods=['POST'], website=True)
    def ws_pedido(self, **kw):
        pedido_nombre = kw['name'];
        #fecha_pedido = kw['fecha_pedido'];
        importe = kw['importe'];
        rfc_compania = kw['compania_cmb'];
        pedido = self.buscaPedido(pedido_nombre, importe, rfc_compania, None);


        retorno_pedido = {};
        retorno_pedido["name"] = pedido.referencia;
        retorno_pedido["compania"] = pedido.company_id.name;
        retorno_pedido["rfc_compania"] = pedido.company_id.company_registry;
        retorno_pedido["importe"] = pedido.amount_total;
        retorno_pedido["cliente_rfc"] = pedido.partner_id.rfc_cliente;
        retorno_pedido["cliente_mail"] = pedido.partner_id.email;
        #retorno_pedido["importe"] = pedido.amount_total;

        return [{'status': 'test',
                 'pedido': retorno_pedido,
                 }]




    @http.route('/autofactura/generar_factura', type='http', methods=['POST'], auth="public", website=True, csrf=False)
    def generar_factura(self, **kw):


        pedido_nombre = kw['pedido'];
        fecha_pedido = "";
        importe = kw['importe'];
        emisor_rfc = kw['emisor_rfc'];




        receptor_razon_social = kw['receptor_razon_social'];
        receptor_rfc = kw['receptor_rfc'];
        receptor_email = kw['receptor_email'];

        #mail = kw['pedido.partner_id.email'];

        uso_cmb = kw["uso_cmb"];
        #metodo_pago_cmb = kw["metodo_pago_cmb"];
        metodo_pago_cmb = "PUE";
        forma_pago_cmb = kw["forma_pago_cmb"];

        pedido_pos = False;
        #Busca nuévamente el pedido
        inv_obj = http.request.env['account.invoice']

        pedido = self.buscaPedido(pedido_nombre, importe, emisor_rfc, fecha_pedido)
        if pedido == None:
            pedido = self.buscaPedidoPOS(pedido_nombre, importe, emisor_rfc, None)
            if pedido == None:
                return http.request.render('autofactura.pedido_no_encontrado', {
                    'mensaje':'No se encontró el pedido solicitado'
                })

            pedido_pos = True;



        # pedido = self.buscaPedido(pedido_nombre, importe, emisor_rfc, fecha_pedido)
        # if pedido == None:
        #     return http.request.render('autofactura.pedido_no_encontrado', {
        #         'mensaje':'No se encontró el pedido solicitado'
        #     })


        arr_facturas = inv_obj.sudo().search([('origin','=',pedido_nombre)]);
        if len(arr_facturas) >0:
            return http.request.render('autofactura.pedido_no_encontrado', {
                'mensaje':'El pedido solicitado ya cuenta con factura.'
            })




        UsoCfdi = http.request.env['catalogos.uso_cfdi'];
        arr_uso_cfdi = UsoCfdi.sudo().search([('c_uso_cfdi', '=', uso_cmb)])
        if len(arr_uso_cfdi) == 0:
            return http.request.render('autofactura.pedido_no_encontrado', {
                'mensaje':'No se encontró el Uso de CFDI solicitado'
            })

        uso_cfdi = arr_uso_cfdi[0];

        #Método de pago
        MetodoPago = http.request.env['catalogos.metodo_pago'];
        arr_metodo_pago = MetodoPago.sudo().search([('c_metodo_pago', '=', metodo_pago_cmb)])
        if len(arr_metodo_pago) == 0:
            return http.request.render('autofactura.pedido_no_encontrado', {
                'mensaje':'No se encontró el Método de  pago solicitado'
            })

        metodo_pago = arr_metodo_pago[0];


        #Forma de pago
        FormaPago = http.request.env['catalogos.forma_pago'];
        arr_forma_pago = FormaPago.sudo().search([('c_forma_pago', '=', forma_pago_cmb)])
        if len(arr_forma_pago) == 0:
            return http.request.render('autofactura.pedido_no_encontrado', {
                'mensaje':'No se encontró la Forma de  pago solicitado'
            })

        forma_pago = arr_forma_pago[0];


        journal_id = http.request.env['account.invoice'].sudo().default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(('Please define an accounting sale journal for this company.'))

        # referencia = pedido.name;
        # if pedido.client_order_ref != None and pedido.client_order_ref != False:
        #     referencia = pedido.client_order_ref;

        # codigo_search = http.request.env['cfdi.codigo_postal'].sudo().search([('c_codigopostal', '=',pedido.company_id.zip)])
        # if codigo_search.id== False:
        #     raise ValidationError("Compruebe el Codigo Postal colocado en la configuracion de la compania ya que no se encuentra en el catalogo del sat")

        inv_obj = http.request.env['account.invoice']

        atributos = {};
        atributos["name"] = receptor_razon_social;
        atributos["cfdi"] = True;
        atributos["rfc_cliente"] = receptor_rfc;
        atributos["email"] = receptor_email;

        #Actualiza datos del cliente, con los datos introducidos
        if pedido_pos == False:#Si es pedido de venta directa
            cliente_id = pedido.partner_id.id;
            cliente = http.request.env['res.partner'].sudo().search([('id', '=', cliente_id)]);
            #print cliente;
            cliente.write(atributos)
            invoices = pedido.action_invoice_create();
            invoice_id = invoices[0];
            invoice = http.request.env['account.invoice'].sudo().browse(invoice_id)
            #invoice_id = invoice.id;




        if pedido_pos == True:#Si es pedido del punto de venta
            cliente_id = pedido.partner_id;
            if cliente_id.id != False and cliente_id.id != None:#Si no tiene cliente, lo crea
                cliente = http.request.env['res.partner'].sudo().search([('id', '=', cliente_id.id)]);
                cliente.write(atributos)
            else:
                cliente = http.request.env['res.partner'];

                #Busca al cliente por RFC
                arr_clientes = cliente.sudo().search([('rfc_cliente', '=', receptor_rfc)]);
                if arr_clientes!= None and len(arr_clientes)>0:
                    cliente = arr_clientes[0];
                else:
                    cliente = cliente.sudo().create(atributos);


            pedido.write({"partner_id" : cliente.id});

            res = pedido.action_pos_order_invoice();
            invoice = http.request.env['account.invoice'].sudo().browse(res['res_id'])
            invoice_id = invoice.id;



        arr_facturas = inv_obj.sudo().search([('id','=',invoice_id)]);
        if len(arr_facturas) == 0:
            return http.request.render('autofactura.pedido_no_encontrado', {
                'mensaje':'La factura se creó, pero no fué timbrada, reportar al administrador'
            })




        #print(invoice)
        invoice["uso_cfdi_id"] = uso_cfdi;
        invoice["metodo_pago_id"] = metodo_pago;
        invoice["forma_pago_id"] = forma_pago;
        invoice.date_invoice = datetime.now()
        #invoice.destinatarios.append(mail);



        #Timbra la factura
        try:
            invoice.action_invoice_open();
        except Exception as e:
            self._logger.info(e)
            http.request.env.cr.rollback()
            traceback.print_exc()
            return http.request.render('autofactura.pedido_no_encontrado', {
                    'mensaje':'Ha ocurrido un error al generar la factura, reportar al administrador de la página.'
                })


        # return http.request.render('autofactura.pedido_no_encontrado', {
        #         'mensaje':'No Raise'
        #     })


        # invoice_id = 32;
        # arr_facturas = inv_obj.sudo().search([('id','=',invoice_id)]);
        # if len(arr_facturas) == 0:
        #     return http.request.render('autofactura.pedido_no_encontrado', {
        #         'mensaje':'La factura se creó, pero no fué timbrada, reportar al administrador'
        #     })
        #
        # invoice = arr_facturas[0];

        #factura_timbrada
        url_parte = http.request.env['catalogos.configuracion'].sudo().search([('url', '!=', '')])
        invoice = arr_facturas[0];

        # string=str(str(invoice.fac_id))
        # algorithim=hashlib.md5()
        # algorithim.update(string)
        # encrypted=algorithim.hexdigest()

        factura=str(invoice.fac_id)
        #string=str(contrasena.encode("utf-8"))
        algorithim=hashlib.md5()
        algorithim.update(factura.encode("utf-8"))
        encrypted=algorithim.hexdigest()

        url_descarga_pdf = url_parte.url+invoice.pdf+encrypted
        url_descarga_xml = url_parte.url+invoice.xml+encrypted



        return http.request.render('autofactura.factura_timbrada', {
            'factura': invoice,
            'url_descarga_pdf':url_descarga_pdf,
            'url_descarga_xml':url_descarga_xml,
        })


    #@api.multi
    @http.route('/autofactura/descargar_factura_pdf', type='http', methods=['POST'], auth="public", website=True, csrf=False)
    def descargar_factura_pdf(self, **kw):
        invoice_id = kw['fac_id'];
        inv_obj = http.request.env['account.invoice']
        arr_facturas = inv_obj.sudo().search([('fac_id','=',invoice_id)]);
        if len(arr_facturas) == 0:
            return http.request.render('autofactura.pedido_no_encontrado', {
                'mensaje':'La factura se creó, pero no fué timbrada, reportar al administrador'
            })

        invoice = arr_facturas[0];

        factura_id = invoice['fac_id'];
        url_parte = http.request.env['catalogos.configuracion'].sudo().search([('url', '!=', '')])

        inv_obj = http.request.env['account.invoice']
        arr_facturas = inv_obj.sudo().search([('fac_id','=',factura_id)]);
        if len(arr_facturas) == 0:
            return http.request.render('autofactura.pedido_no_encontrado', {
                'mensaje':'No se encontró la pinchi factura'
            })

        invoice = arr_facturas[0];

        string=str(str(invoice.fac_id).encode("utf-8"))
        algorithim=hashlib.md5()
        algorithim.update(string)
        encrypted=algorithim.hexdigest()

        url_descarga_pdf = url_parte.url+invoice.pdf+encrypted

        return {
                  'name'     : 'Go to website',
                  'res_model': 'ir.actions.act_url',
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'current',
                  'url'      : url_descarga_pdf
               }


        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': url_descarga_pdf,
        #     'target': 'new',
        # }



    def buscaPedido(self, name, total, rfc_compania, fecha):
        SaleOrder = http.request.env['sale.order']
        #pedidos = self.env['sale.order'].search([('name', '=', pedido_nombre)])
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
        #d1 = datetime.strftime(fecha, "%Y-%m-%d %H:%M:%S")
        #d2 = datetime.strftime(fecha, "%Y-%m-%d 24:59:59")


        #pedidos = SaleOrder.search([('name', '=', pedido_nombre), ('amount_total', '=', float(importe)), ('confirmation_date', '>=', d1), ('confirmation_date', '<=', d2)])
        #pedidos = PosOrder.sudo().search([('pos_reference', '=', name), ('amount_total', '=', float(total))])
        #pedidos = PosOrder.sudo().search([('pos_reference', '=', _("Order ")+name), ('amount_total', '=', float(total))])
        pedidos = PosOrder.sudo().search([('pos_reference', '=', _("Order ")+name)])

        if len(pedidos) == 0:
            return None;

        #for pedido in pedidos:
        #    if rfc_compania == pedido.company_id.company_registry:
        #        return pedido;
        if float(total) != pedidos[0].amount_total:
            return None;

        return pedidos[0];

