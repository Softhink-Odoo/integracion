# -*- coding: utf-8 -*-
from decimal import Decimal
import pytz
import datetime
import re
import time
import json
import hashlib
import requests
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from dateutil.tz import tzlocal
from odoo import api, fields, models

import logging
from odoo import models, fields, api,_

class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    _logger = logging.getLogger(__name__)

    @api.model
    def default_get(self, fields):
        print("Entra a Default get")
        rec = super(AccountPayment, self).default_get(fields)
        rec['ref'] = rec['communication'];
        print(rec)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        # if invoice_defaults and len(invoice_defaults) == 1:
        #     invoice = invoice_defaults[0]
        #     rec['communication'] = invoice['reference'] or invoice['name'] or invoice['number']
        #     rec['currency_id'] = invoice['currency_id'][0]
        #     rec['payment_type'] = invoice['type'] in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
        #     rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
        #     rec['partner_id'] = invoice['partner_id'][0]
        #     rec['amount'] = invoice['residual']
        return rec

    id_banco_seleccionado= fields.Integer('id_banco_seleccionado')
    formadepagop_id = fields.Many2one('catalogos.forma_pago',string='Forma de pago')
    moneda_p = fields.Many2one('res.currency',string='moneda_p')
    tipocambiop = fields.Char('Tipo de cambio',readonly=True)
    uuid = fields.Char(string="UUID",readonly=True)
    #Monto

    #@api.one
    def establecer_referencia_de_pago(self):
        print "establece"
        invoice = self.env['account.invoice'].browse(self._context.get('active_ids'))
        print invoice
        referencia_factura= invoice.number
        #self.communication = ksks
        return referencia_factura


    no_operacion = fields.Char('No. de operacion',help='Se puede registrar el número de cheque, número de autorización, '
    +'número de referencia,\n clave de rastreo en caso de ser SPEI, línea de captura o algún número de referencia \n o '
    +'identificación análogo que permita identificar la operación correspondiente al pago efectuado.')
    rfc_emisor_cta_ord = fields.Char('RFC Emisor Institucion Bancaria')
    nom_banco_ord_ext_id = fields.Many2one('catalogos.bancos',string='Banco emisor')
    cta_ordenante = fields.Char('Cuenta Ordenante')
    rfc_emisor_cta_ben = fields.Char(string='RFC Emisor Cuenta Beneficiario',readonly=True)
    cta_beneficiario = fields.Char(string='Cuenta Beneficiario',readonly=True)
    parcial_pagado = fields.Char(string='No. Parcialidad')
    ref = fields.Char(string='Referencia Factura',default=establecer_referencia_de_pago)

    @api.one
    @api.depends('communication')
    def Timbrara_Pago(self):
        invoice = self.env['account.invoice'].browse(self._context.get('active_ids'))
        for record in invoice:
            print record.fac_timbrada;
            if record.fac_timbrada == 'Timbrada':
                self.timbrar_pago= True
            else:
                self.timbrar_pago=False
            #if record.metodo_pago_id.c_metodo_pago=="PPD":
            #    self.timbrar_pago= True
            #else:
            #    self.timbrar_pago=False
        return self.timbrar_pago

    timbrar_pago = fields.Boolean(string='Timbrar Factura',store=True,compute=Timbrara_Pago)

    ocultar = fields.Boolean(string='Meeeen',store=True, compute="_compute_ocultar",track_visibility='onchange')

    sustituye_pago = fields.Boolean(string='¿Este pago sustituye otro?',default = False,
                                    help='Se utiliza para cuando el pago en cuestión, va a sustituir algún pago que ya fué cancelado')
    pago_sustituye = fields.Many2one('account.move' ,string='Pago a sustituir',
                                     help='Referencia con el pago que se va a sustituir')


    @api.onchange('currency_id')
    def _onchange_actualiza_tipo_cambio(self):
        print "Entra"
        self.tipocambiop = self.currency_id.rate
        print self.tipocambiop

    @api.one
    @api.depends('formadepagop_id.c_forma_pago')
    def _compute_ocultar(self):
        if self.formadepagop_id.c_forma_pago == "01":
            self.ocultar = True
        else:
            self.ocultar = False

    @api.onchange('nom_banco_ord_ext_id')
    def _onchange_establecer_banco_emisor(self):
        self.rfc_emisor_cta_ord = self.nom_banco_ord_ext_id.rfc_banco
        self.id_banco_seleccionado = self.nom_banco_ord_ext_id.id
            

    @api.onchange('journal_id')
    def _onchange_actualiza_datos_bancarios(self):
        if self.journal_id.type == "bank":
            self.cta_beneficiario=self.journal_id.bank_acc_number
            self.rfc_emisor_cta_ben=self.journal_id.rfc_institucion_bancaria
            self.tipocambiop = self.currency_id.rate

    # Coloca la informacion del metodo onchange que se encuentra como readonly
    @api.constrains('journal_id')
    def Validar_Forma_Pago(self):

        if self.timbrar_pago == False:
            return;

        # Valida que haya elegido una forma de pago
        if self.payment_type == "inbound":
            if self.ref != False:
                if self.formadepagop_id.id != False:
                    #Valida el ingreso de datos Bancarios
                    if self.formadepagop_id.descripcion != "Efectivo":
                        if self.journal_id.type == "bank":
                            if self.formadepagop_id.rfc_emisor_cta_benef != "No":
                                self.cta_beneficiario = self.journal_id.bank_acc_number
                                """Esta linea de codigo fue comentada ya que apartir de ahora de utilizara un catalago de bancos precargado.
                                Anteriormente utilizaba del banco del diario para realizar este paso de informacion, pero con la nueva forma
                                a quedado obsoleto por lo que ha sido comentado en caso de que sea requerido para instalaciones anteriores"""
                                #self.nom_banco_ord_ext_id = self.journal_id.bank_id.name
                                self.rfc_emisor_cta_ben = self.journal_id.rfc_institucion_bancaria
                                self.tipocambiop = self.currency_id.rate
                            if self.formadepagop_id.rfc_emisor_cta_benef != "No":
                                # Valida el patron de la cuenta Beneficiara
                                patron_cta_benef = self.formadepagop_id.patron_cta_benef
                            # Valida que la Cuenta Beneficiaria no este vacia
                            if self.cta_beneficiario != False:
                                if patron_cta_benef != "No":
                                    rule_patron_cta_benef = re.compile(patron_cta_benef)
                                    if not rule_patron_cta_benef.search(self.cta_beneficiario):
                                        msg = "Formato de Cuenta Beneficiaria Incorrecto para la forma de pago: "+str(self.formadepagop_id.descripcion)
                                        raise ValidationError(msg)
                            # Valida el patron de la cuenta ordenante
                            patron_cta_ordenante = self.formadepagop_id.patron_cta_ordenante
                            if self.cta_ordenante != False:
                                if patron_cta_ordenante != "No":
                                    rule_patron_cta_ordenante = re.compile(patron_cta_ordenante)
                                    if not rule_patron_cta_ordenante.search(self.cta_ordenante):
                                        msg = "Formato de Cuenta Ordenante Incorrecto para la forma de pago: " + str(self.formadepagop_id.descripcion)
                                        raise ValidationError(msg)
                else:
                    raise ValidationError("No ha ingresado la forma de pago")

    def Validar_y_Timbrar_Pago(self):
        self.post_2(True)

    def Validar_Pago(self):
        self.post_2(False)

    @api.multi
    def post_2(self,timbrar):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry_2(amount,timbrar)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})

    def _create_payment_entry_2(self, amount,timbrar):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        #self.nom_banco_ord_ext_id = self.id_banco_seleccionado
        residual_antes_de_pago = self.invoice_ids.residual
        self.tipocambiop = self.currency_id.rate
        moneda_extranjera = False
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            #if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
            #amount_currency = moneda traducida a la factura
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
        move = self.env['account.move'].create(self._get_move_vals())
        var_extra = amount_currency
        #Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        #Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
            # the writeoff debit and credit must be computed from the invoice residual in company currency
            # minus the payment amount in company currency, and not from the payment difference in the payment currency
            # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
            total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
            total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount, self.company_id.currency_id)
            if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                amount_wo = total_payment_company_signed - total_residual_company_signed
            else:
                amount_wo = total_residual_company_signed - total_payment_company_signed
            # Align the sign of the secondary currency writeoff amount with the sign of the writeoff
            # amount in the company currency
            if amount_wo > 0:
                debit_wo = amount_wo
                credit_wo = 0.0
                amount_currency_wo = abs(amount_currency_wo)
            else:
                debit_wo = 0.0
                credit_wo = -amount_wo
                amount_currency_wo = -abs(amount_currency_wo)
            writeoff_line['name'] = _('Counterpart')
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit']:
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit']:
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo
        self.invoice_ids.register_payment(counterpart_aml)

        #Write counterpart lines
        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        if self.invoice_ids.currency_id.id != self.currency_id.id:
            imp_pagado_currency = var_extra
            moneda_extranjera = True
            if self.invoice_ids.currency_id.id == self.company_id.currency_id.id:
                imp_pagado_currency = credit
        else:
            imp_pagado_currency = credit
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
        aml_obj.create(liquidity_aml_dict)
        
        if self.payment_type == "inbound":
            # Incremento el numero de parcilidad
            par = str(int(self.invoice_ids.no_parcialidad) + 1)
            self.invoice_ids.no_parcialidad = par

            #Envio la informacion al modelo account.move

            self.tipocambiop = self.currency_id.rate

            move.move_no_parcialidad = par
            move.move_formadepagop_id = self.formadepagop_id
            move.move_moneda_p = self.currency_id.id
            move.move_tipocambiop = (1/float(self.tipocambiop))
            move.move_uuid_ref = self.invoice_ids.uuid
            move.move_rfc_emisor_cta_ben = self.rfc_emisor_cta_ben
            move.move_cta_beneficiario = self.cta_beneficiario
            move.move_parcial_pagado = self.parcial_pagado
            move.move_imp_saldo_ant = residual_antes_de_pago
            if moneda_extranjera == True and self.invoice_ids.currency_id.id != self.company_id.currency_id.id:
                move.move_imp_pagado = -(imp_pagado_currency)
                move.move_tipocambiop = 1/(self.invoice_ids.currency_id.rate)
            else:
                move.move_imp_pagado = imp_pagado_currency
            move.move_imp_saldo_insoluto = (Decimal(move.move_imp_saldo_ant))-(Decimal(move.move_imp_pagado))
            move.move_rfc_emisor_cta_ord = self.rfc_emisor_cta_ord
            #move.move_nom_banco_ord_ext_id = self.nom_banco_ord_ext_id.id
            move.move_cta_ordenante = self.cta_ordenante
            move.ref_factura = self.ref
            move.move_no_operacion = self.no_operacion
            self._logger.info(self.nom_banco_ord_ext_id)
            move.move_nom_banco_ord_ext_id   =self.nom_banco_ord_ext_id;


            move.sustituye_pago = self.sustituye_pago;
            move.pago_sustituye = self.pago_sustituye;


            #move.move_payment_date = self.payment_date;
            if timbrar == True:
                move.timbrar_pago()
        move.post()
        return move



class AccountMove(models.Model):
    _name = 'account.move'
    _inherit  = 'account.move'

    _logger = logging.getLogger(__name__)

    def establecer_uso_de_cfdi(self):
        uso = self.env['catalogos.uso_cfdi'].search([('id', '=', '22')])
        return uso

    move_no_parcialidad = fields.Char(string='No. Parcialidad')
    move_formadepagop_id = fields.Many2one('catalogos.forma_pago',string='Forma de pago')
    move_moneda_p = fields.Many2one('res.currency',string='Moneda')
    move_tipocambiop = fields.Char('Tipo de cambio')
    move_uuid = fields.Char(string="UUID del Pago", readonly=True)
    move_uuid_ref = fields.Char(string="UUID Relacionado", readonly=True)
    #Monto
    move_rfc_emisor_cta_ben = fields.Char('RfcEmisorCtaBen')
    move_cta_beneficiario = fields.Char('CtaBeneficiario')
    move_rfc_emisor_cta_ord = fields.Char('RFC Emisor Cuenta Ord')
    move_nom_banco_ord_ext_id = fields.Many2one('catalogos.bancos',string='Banco')
    move_cta_ordenante = fields.Char('Cuenta Ordenante')
    move_rfc_emisor_cta_ben = fields.Char('RFC Emisor Cuenta Beneficiario')
    move_cta_beneficiario = fields.Char('Cuenta Beneficiario')
    move_no_operacion = fields.Char('No. Operacion', help='Se puede registrar el número de cheque, número de autorización, '
    + 'número de referencia,\n clave de rastreo en caso de ser SPEI, línea de captura o algún número de referencia \n o '
    + 'identificación análogo que permita identificar la operación correspondiente al pago efectuado.')
    move_timbrada = fields.Char('CFDI',default="Sin Timbrar",readonly=True)
    fac_id = fields.Char()
    pdf = "Factura?Accion=descargaPDF&fac_id=";
    xml = "Factura?Accion=ObtenerXML&fac_id=";
    move_uso_cfdi_id = fields.Many2one('catalogos.uso_cfdi',string='Uso CFDI',default=establecer_uso_de_cfdi)
    ref_factura = fields.Char(string='Referencia Factura')
    move_imp_pagado = fields.Monetary('Importe Pagado')
    move_imp_saldo_ant = fields.Monetary('Importe Saldo Anterior')
    move_imp_saldo_insoluto = fields.Monetary('Importe Saldo Insoluto')
    #move_payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, copy=False)

    sustituye_pago = fields.Boolean(string='¿Este pago sustituye otro?',default = False,
                                    help='Se utiliza para cuando el pago en cuestión, va a sustituir algún pago que ya fué cancelado')
    pago_sustituye = fields.Many2one('account.move' ,string='Pago a sustituir',
                                     help='Referencia con el pago que se va a sustituir')


    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted'), ('canceled', 'Canceled'), ('replaced', 'Replaced')], string='Status',
      required=True, readonly=True, copy=False, default='draft',
      help='All manually created new journal entries are usually in the status \'Unposted\', '
           'but you can set the option to skip that status on the related journal. '
           'In that case, they will behave as journal entries automatically created by the '
           'system on document validation (invoices, bank statements...) and will be created '
           'in \'Posted\' status.')




    def Puede_Timbrar(self):
        #invoice = self.env['account.invoice'].browse(self._context.get('active_ids'))
        self._logger.info(self.ref)
        invoice = self.env['account.invoice'].search([('number', '=', self.ref)])
        for record in invoice:
            self._logger.info(record.fac_timbrada)
            if record.fac_timbrada == 'Timbrada' :
                self.move_puede_timbrar= True
            else:
                self.move_puede_timbrar=False
            #if record.metodo_pago_id.c_metodo_pago=="PPD":
            #    self.timbrar_pago= True
            #else:
            #    self.timbrar_pago=False
        return self.move_puede_timbrar

    move_puede_timbrar = fields.Boolean(string='Timbrar Factura',store=False,compute=Puede_Timbrar)


    @api.onchange('move_nom_banco_ord_ext_id')
    def _onchange_establecer_banco_emisor(self):
        print self.move_nom_banco_ord_ext_id.rfc_banco
        self.move_rfc_emisor_cta_ord = self.move_nom_banco_ord_ext_id.rfc_banco
        #self.id_banco_seleccionado = self.move_nom_banco_ord_ext_id.id



    @api.multi
    def descargar_factura_pdf(self):

        url_parte = self.env['catalogos.configuracion'].search([('url', '!=', '')])
        url_descarga_pdf = url_parte.url + self.pdf + self.fac_id
        return {
            'type': 'ir.actions.act_url',
            'url': url_descarga_pdf,
            'target': 'new',
        }

    @api.multi
    def descargar_factura_xml(self):

        url_parte = self.env['catalogos.configuracion'].search([('url', '!=', '')])
        url_descarga_xml = url_parte.url + self.xml + self.fac_id
        print url_descarga_xml
        return {
            'type': 'ir.actions.act_url',
            'url': url_descarga_xml,
            'target': 'new',
        }

    def timbrar_pago(self):
        url_parte = self.env['catalogos.configuracion'].search([('url', '!=', '')])
        factura = self.env['account.invoice'].search([('number', '=', self.ref_factura)])
        url = str(url_parte.url) + "webresources/FacturacionWS/Facturar"

        #emisor_regimen_fiscal_nombre = self.env['res.company'].search([('property_account_position_id.name','=',self.env.user.company_id.property_account_position_id.name)])
        #emisor_regimen_fiscal_key = self.env['res.company'].search([('property_account_position_id.c_regimenfiscal','=',self.env.user.company_id.property_account_position_id.c_regimenfiscal)])
        
        impuesto_iva = ""
        lineas = []
        for lineas_de_factura in factura.invoice_line_ids:
            for taxs in lineas_de_factura.invoice_line_tax_ids:
                if taxs.tipo_impuesto_id.descripcion == "IVA":
                    impuesto_iva = taxs.tasa_o_cuota_id.valor_maximo


        #Datos del Usuario de Conectividad
        usuario = url_parte.usuario
        contrasena = url_parte.contrasena
        string = str(contrasena.encode("utf-8"))
        # crea el algoritmo para encriptar la informacion
        algorithim = hashlib.md5()
        # encripta la informacion
        algorithim.update(string)
        # La decodifica en formato hexadecimal
        encrypted = algorithim.hexdigest()
        ts = time.time()
        tz = pytz.timezone('America/Monterrey')
        ct = datetime.datetime.now(tz=tz).strftime('%H:%M:%S')
        tiempo = time.strftime("%H:%M:%S")
        timestamp = time.strftime('%Y/%m/%d %H:%M:%S')
        #fecha_pago = factura.date_invoice+"T"+str(ct)
        fecha_pago = self.date+"T"+str(ct)

        if self.move_nom_banco_ord_ext_id == False:
            self.move_nom_banco_ord_ext_id = ""

        if self.move_cta_ordenante == False:
            self.move_cta_ordenante = ""

        if self.move_rfc_emisor_cta_ben == False:
            self.move_rfc_emisor_cta_ben = ""

        if self.move_cta_beneficiario == False:
            self.move_cta_beneficiario = ""

        if self.move_rfc_emisor_cta_ben == False:
            self.move_rfc_emisor_cta_ben = ""

        print url
        #Estructura Json
        data = {
            "factura": {
                "fecha_facturacion": factura.date_invoice,
                "odoo_contrasena": encrypted,
                "fac_tipo_cambio": 1,
                "fac_moneda": "XXX",
                "fac_tipo_comprobante": "P",
                "fac_importe": 0,
                "receptor_uso_cfdi": self.move_uso_cfdi_id.c_uso_cfdi,
                "user_odoo": url_parte.usuario,
                "receptor": {
                    "numero_ext": factura.partner_id.numero_ext,
                    "receptor_id": factura.rfc_cliente_factura,
                    "estado": factura.partner_id.state_id.name.encode('utf-8'),
                    "compania": factura.partner_id.name.encode('utf-8'),
                    "ciudad": factura.partner_id.city.encode('utf-8'),
                    "calle": factura.partner_id.street.encode('utf-8'),
                    "correo": factura.partner_id.email.encode('utf-8'),
                    "NIF": factura.partner_id.nif,
                    "codigopostal": factura.partner_id.zip,
                    "colonia": factura.partner_id.colonia.encode('utf-8')
                },
                "fac_lugar_expedicion": factura.codigo_postal_id.c_codigopostal,
                "fac_porcentaje_iva": impuesto_iva,
                "conceptos": [{
                    "con_subtotal": "0.0",
                    "con_valor_unitario": "0.0",
                    "con_importe": "0.0",
                    "con_cantidad": "1",
                    "con_unidad_clave": "ACT",
                    "con_clave_prod_serv": "84111506",
                    "con_descripcion": "Pago",
                    "con_total": "0.0"
                }],
                "emisor_id": str(self.env.user.company_id.company_registry),
                "fac_no_orden": factura.number,
                "fac_emisor_regimen_fiscal_descripcion": self.env.user.company_id.property_account_position_id.name,
                "fac_emisor_regimen_fiscal_key": self.env.user.company_id.property_account_position_id.c_regimenfiscal,
                "pago": {
                    "fecha_pago": fecha_pago,
                    "forma_de_pago": str(self.move_formadepagop_id.c_forma_pago),
                    "moneda": str(self.move_moneda_p.name),
                    "tipo_cambio": str(self.move_tipocambiop),
                    "monto": str(self.move_imp_pagado),
                    "num_operacion": "01",
                    #"rfc_emisor_cta_ord": str(factura.partner_id.nif),
                    "rfc_emisor_cta_ord": str(self.move_rfc_emisor_cta_ord),
                    "nom_banco_ord_ext_id": str(self.move_nom_banco_ord_ext_id.c_nombre),
                    "cta_ordenante": str(self.move_cta_ordenante),
                    "rfc_emisor_cta_ben": str(self.move_rfc_emisor_cta_ben),
                    "cta_beneficiario": str(self.move_cta_beneficiario),
                    "documentos": [
                        {
                            "id_documento": str(factura.uuid),
                            "serie": "A4055",
                            "folio": "2154",
                            "moneda_dr": str(factura.currency_id.name),
                            "tipo_cambio_dr": "1",
                            "metodo_de_pago_dr": 'PPD',
                            "num_parcialidad": str(self.move_no_parcialidad),
                            "imp_pagado": str(self.move_imp_pagado),
                            "imp_saldo_ant": str(self.move_imp_saldo_ant),
                            "imp_saldo_insoluto": str(self.move_imp_saldo_insoluto)
                        }
                    ]
                }
            }
        }

        #CFDIRelacionados (Para reemplazo de pagos)
        if self.sustituye_pago == True:
            cfdi_relacionados = []
            cfdi_relacionado = {
               "uuid": self.pago_sustituye.move_uuid
            }
            cfdi_relacionados.append(cfdi_relacionado)
            data["factura"]["cfdi_relacionados"] = cfdi_relacionados;
            data["factura"]["fac_tipo_relacion"] = "04";

            #Actualiza el otro a Reemplazado
            self.pago_sustituye.write({"state" : "replaced"});


        headers = {
            'content-type': "application/json", 'Authorization': "Basic YWRtaW46YWRtaW4="
        }
        self._logger.info(data)
        response = requests.request("POST", url, data=json.dumps(data), headers=headers)

        print((response.text).encode('utf-8'))
        json_data = json.loads(response.text)
        if json_data['result']['success'] == 'true':
            self.move_timbrada = 'Timbrada'
            # En caso de recibir una respuesta positiva anexa el uuid al formulario de la factura timbrada
            self.move_uuid = json_data['result']['uuid']
            self.fac_id = json_data['result']['fac_id']
            print self.fac_id
        else:
            raise ValidationError(json_data['result']['message'])

    @api.multi
    def cancelar_pagos_timbrada(self):
        for linea in self.line_ids:
            linea.remove_move_reconcile();

        self.button_cancel();

        # factura =self.env['account.invoice'].search([('id','=',73)])
        # print(factura.id)
        # return {
        #     'name': _('Payments'),
        #     #'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('account.view_account_payment_invoice_form').id,
        #     'res_model': 'account.payment',
        #     'target': 'new',
        #     'context': {'default_invoice_ids': [(4, None, None)]},
        #     #'flags': {'initial_mode': 'edit'},
        #     'type': 'ir.actions.act_window',
        # }
        #
        #
        #
        #
        # #Busca el pago con el que se generó el movimiento y lo abre para que lo pueda timbrar sustituyendo el actual
        # return {
        #     'name': _('Crear pago'),
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('sft-facturacion.account_payment_sat_invoice_view').id,
        #     'res_model': 'account.payment',
        #     'context': self.env.context,
        #     'type': 'ir.actions.act_window',
        #     'nodestroy': True,
        #     'target': 'new',
        #     'views': [(False, 'form')],
        #     #'res_id': None,
        # }

        #
        # return {
        #        'type': 'ir.actions.act_window',
        #        'name': 'Form heading',
        #        'view_mode': 'form',
        #        'view_type': 'form',
        #        'view_id': "payment.view_account_payment_invoice_form_inherit_payment",
        #        'res_model': 'account.payment',
        #        'nodestroy': True,
        #        #'res_id': this.id, # assuming the many2one
        #        'target':'new',
        #        'context': self.env.context,
        # }
        #
        # return


        url_parte = self.env['catalogos.configuracion'].search([('url', '!=', '')])
        url = str(url_parte.url)+"webresources/FacturacionWS/Cancelar"
        data = {
         "uuid": self.move_uuid
        }

        headers = {
           'content-type': "application/json", 'Authorization':"Basic YWRtaW46YWRtaW4="
    }
        self._logger.info(json.dumps(data));
        response = requests.request("POST", url, data=json.dumps(data), headers=headers)
        self._logger.info(response.text );
        json_data = json.loads(response.text)
        if json_data['result']['success'] == 'true' or json_data['result']['success'] == True:
            self.move_timbrada = 'Pago Cancelado'
            self.state = "canceled";
            #Rompe conciliación
            #mode_line.
            #remove_move_reconcile

        else:
            raise ValidationError(json_data['result']['message'])

class AccountJournal(models.Model):
    _name = 'account.journal'
    _inherit  = 'account.journal'

    rfc_institucion_bancaria = fields.Char('RFC Institucion Bancaria',size=12)

    @api.constrains('rfc_institucion_bancaria')
    def ValidarRFCInstitucionBancaria(self):
        if self.rfc_institucion_bancaria!=False:
            if len(self.rfc_institucion_bancaria)!=12:
                raise ValidationError("El RFC %s no tiene la logitud de 12 caracteres para personas Morales que establece el sat" % (self.rfc_institucion_bancaria))
            else:
                patron_rfc = re.compile(r'^([A-ZÑ\x26]{3}([0-9]{2})(0[1-9]|1[0-2])(0[1-9]|1[0-9]|2[0-9]|3[0-1]))((-)?([A-Z\d]{3}))?$')
                if not patron_rfc.search(self.rfc_institucion_bancaria):
                    msg = "Formato RFC de Persona Moral Incorrecto"
                    raise ValidationError(msg)

    @api.constrains('bank_acc_number')
    def ValidarNoCuentaBancaria(self):
        if self.bank_acc_number!=False:
            patron_rfc = re.compile(r'[0-9]{10,11}|[0-9]{15,16}|[0-9]{18}|[A-Z0-9_]{10,50}')
            if not patron_rfc.search(self.bank_acc_number):
                msg = "Formato Incorrecto del No. Cuenta"
                raise ValidationError(msg)

