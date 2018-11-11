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
import math

class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    _logger = logging.getLogger(__name__)

    @api.model
    def default_get(self, fields):
        print("default_get")
        rec = super(AccountPayment, self).default_get(fields)
        #self.imp_saldo_ant = self.invoice_ids.residual;
        context = dict(self._context or {})

        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        if active_model != None:
            invoices = self.env[active_model].browse(active_ids)
            rec['imp_saldo_ant'] = invoices.residual;
            rec['moneda_factura'] = invoices.currency_id.name;
            print(invoices.currency_id.name)
        return rec

    @api.model
    def create(self, vals):
        return super(AccountPayment, self).create(vals)

    @api.one
    def compute_default(self):
        print("compute_default")
        self.imp_saldo_ant = self.invoice_ids.residual;
        self.moneda_factura = self.invoice_ids.invoices.currency_id.name;

    id_banco_seleccionado= fields.Integer('id_banco_seleccionado')
    formadepagop_id = fields.Many2one('catalogos.forma_pago',string='Forma de pago')
    moneda_p = fields.Many2one('res.currency',string='Moneda', default=lambda self: self.env.user.company_id.currency_id)
    moneda_factura = fields.Char(string='Moneda Factura', store=False)
    tipocambiop = fields.Char('Tipo de cambio a MXN')
    tipocambio_oper = fields.Char('Tipo de operacion')
    uuid = fields.Char(string="UUID",readonly=True)
    no_parcialidad = fields.Char(string='No. Parcialidad')
    imp_pagado = fields.Monetary('Importe Pagado')
    #imp_saldo_ant = fields.Monetary('Importe Saldo Anterior', default=lambda self: self.invoice_ids.residual)
    imp_saldo_ant = fields.Monetary('Importe Saldo Anterior')
    imp_saldo_insoluto = fields.Monetary('Importe Saldo Insoluto')
    timbrada = fields.Char('CFDI',default="Sin Timbrar",readonly=True)
    fac_id = fields.Char()
    pdf = "Factura?Accion=descargaPDF&fac_id=";
    xml = "Factura?Accion=ObtenerXML&fac_id=";

    calculo = fields.Char("calculo", store=True, compute='compute_default')



    def establecer_uso_de_cfdi(self):
        uso = self.env['catalogos.uso_cfdi'].search([('id', '=', '22')])
        return uso

    uso_cfdi_id = fields.Many2one('catalogos.uso_cfdi',string='Uso CFDI',default=establecer_uso_de_cfdi)

    #Monto

    #@api.one
    def establecer_referencia_de_pago(self):
        invoice = self.env['account.invoice'].browse(self._context.get('active_ids'))
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
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('canceled', 'Cancelado'), ('replaced', 'Reemplazado')],
                             readonly=True, default='draft', copy=False, string="Status")

    @api.one
    @api.depends('communication')
    def Timbrara_Pago(self):
        invoice = self.env['account.invoice'].browse(self._context.get('active_ids'))
        for record in invoice:
            if record.fac_timbrada == 'Timbrada':
                self.timbrar_pago= True
            else:
                self.timbrar_pago=False
        return self.timbrar_pago

    timbrar_pago = fields.Boolean(string='Timbrar Factura',store=True,compute=Timbrara_Pago)

    ocultar = fields.Boolean(string='Meeeen',store=True, compute="_compute_ocultar",track_visibility='onchange')

    sustituye_pago = fields.Boolean(string='¿Este pago sustituye otro?',default = False,
                                    help='Se utiliza para cuando el pago en cuestión, va a sustituir algún pago que ya fué cancelado')
    pago_sustituye = fields.Many2one('account.payment' ,string='Pago a sustituir',
                                     help='Referencia con el pago que se va a sustituir')

    @api.one
    def _obtPuede_Cancelar(self):
        if self.state == 'posted' and self.timbrada == 'Sin Timbrar':
            self.puede_cancelar = True;
            return True;

        self.puede_cancelar = False;
        return False;

    puede_cancelar = fields.Boolean(string='Puede Cancelar',store=False,compute=_obtPuede_Cancelar)

    @api.one
    def _obtPuede_Editar(self):
        if 'Sin Timbrar' in self.timbrada:
            self.puede_editar = True;
            return True;
        else:
            self.puede_editar = False;
            return False;

    puede_editar = fields.Boolean(string='Puede Editar',store=False,compute=_obtPuede_Editar)

    #@api.onchange('currency_id')
    # @api.onchange('moneda_p')
    # def _onchange_actualiza_tipo_cambio(self):
    #     print self.moneda_p.rate
    #     self.tipocambiop = self.moneda_p.inverse_rate

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
            

    @api.multi
    @api.onchange('journal_id','currency_id')
    def _onchange_actualiza_datos_bancarios(self):
        for record in self:
            self._calculaTipoCambio(record);
            self.GuardaGeneralesPago(record);

    @api.multi
    @api.onchange('amount')
    def _onchange_actualiza_amount(self):
        for record in self:
            self.GuardaGeneralesPago(record);

    @api.multi
    @api.onchange('tipocambiop')
    def _onchangeTipoCambioP(self):
        for record in self:
            self.GuardaGeneralesPago(record);

    @api.multi
    @api.onchange('tipocambio_oper')
    def _onchangeTipoCambioOper(self):
        if "MXN" == self.invoice_ids.currency_id.name:
            self.tipocambiop = self.tipocambio_oper
        for record in self:
            self.GuardaGeneralesPago(record);

    def _calculaTipoCambio(self, record):
        model_currency = self.env['res.currency'];
        record.tipocambio_oper = record.currency_id.round(model_currency.with_context(date=self.payment_date)._get_conversion_rate(record.currency_id, record.invoice_ids.currency_id))

        currency_pesos = model_currency.search([('name', '=', 'MXN')])
        if currency_pesos == None or len(currency_pesos)==0:
            self.tipocambiop = 1;
        else:
            self.tipocambiop =  currency_pesos[0].round(1/model_currency.with_context(date=self.payment_date)._get_conversion_rate(currency_pesos[0],record.currency_id))


    # def _compute_total_invoices_amount(self):
    #     print("_compute_total_invoices_amount")
    #     """ Compute the sum of the residual of invoices, expressed in the payment currency """
    #     if self.tipocambio_oper!= None and self.tipocambio_oper != False:
    #         payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
    #         invoices = self._get_invoices()
    #
    #         if all(inv.currency_id == payment_currency for inv in invoices):
    #             total = sum(invoices.mapped('residual_signed'))
    #         else:
    #             total = 0
    #             for inv in invoices:
    #                 if inv.company_currency_id != payment_currency:
    #                     total += inv.company_currency_id.with_context(date=self.payment_date).compute(inv.residual_company_signed, payment_currency)
    #                 else:
    #                     total += inv.residual_company_signed
    #         return abs(total)
    #     else:
    #         payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
    #         invoices = self._get_invoices()
    #
    #         if all(inv.currency_id == payment_currency for inv in invoices):
    #             total = sum(invoices.mapped('residual_signed'))
    #         else:
    #             total = 0
    #             for inv in invoices:
    #                 if inv.company_currency_id != payment_currency:
    #                     total += inv.company_currency_id.with_context(date=self.payment_date).compute(inv.residual_company_signed, payment_currency)
    #                 else:
    #                     total += inv.residual_company_signed
    #         return abs(total)


    @api.one
    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'tipocambio_oper')
    def _compute_payment_difference(self):
        #print("_compute_payment_difference")
        self.calcula_montos(self.amount)
        if len(self.invoice_ids) == 0:
            return
        if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
            self.payment_difference = self.amount - self._compute_total_invoices_amount()
        else:
            self.payment_difference = self._compute_total_invoices_amount() - self.amount


    # @api.model
    # def compute_amount_fields(self, amount, src_currency, company_currency, invoice_currency=False):
    #     """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
    #     amount_currency = False
    #     currency_id = False
    #     if src_currency and src_currency != company_currency:
    #         amount_currency = amount
    #         amount = src_currency.with_context(self._context).compute(amount, company_currency)
    #         currency_id = src_currency.id
    #     debit = amount > 0 and amount or 0.0
    #     credit = amount < 0 and -amount or 0.0
    #     if invoice_currency and invoice_currency != company_currency and not amount_currency:
    #         amount_currency = src_currency.with_context(self._context).compute(amount, invoice_currency)
    #         currency_id = invoice_currency.id
    #     return debit, credit, amount_currency, currency_id




    #def calcula_montos(self, amount, src_currency, company_currency, invoice_currency=False):
    def calcula_montos(self, amount):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
        amount_currency = False
        currency_id = False
        amount_currency = amount
        #amount = amount_currency * self.tipocambio_oper;
        amount = (Decimal(amount_currency))* (Decimal(self.tipocambio_oper));


        debit = amount > Decimal(0) and amount or Decimal(0.0)
        credit = amount < Decimal(0) and -Decimal(amount) or 0.0
        #print("---------------------------")
        #print(amount)
        return debit, credit, Decimal(amount)

    def _create_payment_entry(self, amount):
        if (self.payment_type == 'outbound'):
            return super(AccountPayment, self)._create_payment_entry(amount);


        #print("_create_payment_entry")
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            #if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        #debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
        debit, credit, amount_currency = self.calcula_montos(amount)
        #print("Importe calculado ")
        #print(amount_currency)
        currency_id = self.invoice_ids[0].currency_id.id;

        move = self.env['account.move'].create(self._get_move_vals())

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
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
        aml_obj.create(liquidity_aml_dict)

        move.post()
        return move


    def _compute_total_invoices_amount(self):
        print("_compute_total_invoices_amount")
        """ Compute the sum of the residual of invoices, expressed in the payment currency """
        payment_currency = self.currency_id or self.journal_id.currency_id or self.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        invoices = self._get_invoices()

        if all(inv.currency_id == payment_currency for inv in invoices):
            total = sum(invoices.mapped('residual_signed'))
        else:
            total = 0
            for inv in invoices:
                if inv.company_currency_id != payment_currency:
                    total += inv.company_currency_id.with_context(date=self.payment_date).compute(inv.residual_company_signed, payment_currency)
                else:
                    total += inv.residual_company_signed
        return abs(total)

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
                                #self.rfc_emisor_cta_ben = self.journal_id.rfc_institucion_bancaria
                                #self.tipocambiop = self.currency_id.inverse_rate
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

    @api.multi
    def Validar_y_Timbrar_Pago(self):
        for record in self:
            if record.payment_type == "inbound":
                if self.state != "posted":
                    self.GuardaGeneralesPago(record);
                    self.post()
                self.generar_timbre();

    def Validar_Pago(self):
        if self.payment_type == "inbound":
            self.GuardaGeneralesPago(self);
            self.post();

        if self.payment_type == "outbound":
            self.post()


    def _validacionTimbre(self):
        if self.sustituye_pago == True and (self.pago_sustituye.id == False or self.pago_sustituye.id == None):
            raise ValidationError("No se ha seleccionado el pago a sustituir")

    def GuardaGeneralesPago(self, record):
        if self.payment_type == "inbound":
            # Incremento el numero de parcilidad
            par = str(int(record.invoice_ids.no_parcialidad) + 1)
            #self.invoice_ids.no_parcialidad = par
            record.no_parcialidad = par
            residual_antes_de_pago = record.invoice_ids.residual
            record.imp_saldo_ant = residual_antes_de_pago;


            if record.journal_id.type == "bank":
                record.cta_beneficiario=record.journal_id.bank_acc_number
                record.rfc_emisor_cta_ben=record.journal_id.rfc_institucion_bancaria
                #self.tipocambiop = self.currency_id.inverse_rate

                record.imp_saldo_ant = record.invoice_ids.residual;
                if record.currency_id == record.invoice_ids.currency_id and record.currency_id.name == 'USD':
                    record.imp_pagado = record.amount;
                else:
                    valor_antes = (Decimal(record.amount))* (Decimal(record.tipocambio_oper));
                    print(valor_antes)
                    record.imp_pagado = (math.floor(valor_antes * 100)/100.0) if round else valor_antes
                    print(record.imp_pagado)
                    #record.imp_pagado = (Decimal(record.amount))* (Decimal(record.tipocambio_oper));

                    #print(math.floor(record.imp_pagado))
                    #record.imp_pagado = record.currency_id.round(record.imp_pagado) if round else record.imp_pagado
                    #record.imp_pagado = (math.floor(record.imp_pagado*100)/100) if round else record.imp_pagado

                record.imp_saldo_insoluto = (Decimal(record.imp_saldo_ant))-(Decimal(record.imp_pagado))


            #record.write({'imp_saldo_insoluto':record.imp_saldo_insoluto})

        #self.moneda_p = self.currency_id.id;


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
        return {
            'type': 'ir.actions.act_url',
            'url': url_descarga_xml,
            'target': 'new',
        }

    def generar_timbre(self):
        self._validacionTimbre();


        url_parte = self.env['catalogos.configuracion'].search([('url', '!=', '')])
        url = str(url_parte.url) + "webresources/FacturacionWS/Facturar"

        factura = self.env['account.invoice'].search([('number', '=', self.ref)])

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
        fecha_pago = self.payment_date+"T"+str(ct)

        if self.nom_banco_ord_ext_id == False:
            self.nom_banco_ord_ext_id = ""

        if self.cta_ordenante == False:
            self.cta_ordenante = ""

        if self.rfc_emisor_cta_ben == False:
            self.rfc_emisor_cta_ben = ""

        if self.cta_beneficiario == False:
            self.cta_beneficiario = ""

        if self.rfc_emisor_cta_ben == False:
            self.rfc_emisor_cta_ben = ""


        #Estructura Json
        data = {
            "factura": {
                "fecha_facturacion": factura.date_invoice,
                "odoo_contrasena": encrypted,
                "fac_tipo_cambio": 1,
                "fac_moneda": "XXX",
                "fac_tipo_comprobante": "P",
                "fac_importe": 0,
                "receptor_uso_cfdi": self.uso_cfdi_id.c_uso_cfdi,
                "user_odoo": url_parte.usuario,
                "receptor": {
                    "receptor_id": factura.rfc_cliente_factura,
                    "NIF": factura.partner_id.nif,
                    "correo": factura.partner_id.email.encode('utf-8'),

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
                "fac_no_orden": self.name,
                "fac_emisor_regimen_fiscal_descripcion": self.env.user.company_id.property_account_position_id.name,
                "fac_emisor_regimen_fiscal_key": self.env.user.company_id.property_account_position_id.c_regimenfiscal,
                "pago": {
                    "fecha_pago": fecha_pago,
                    "forma_de_pago": str(self.formadepagop_id.c_forma_pago),
                    "moneda": str(self.currency_id.name),
                    "tipo_cambio": str(self.tipocambiop),
                    #"monto": str(self.imp_pagado),
                    "monto": str(self.amount),
                    "num_operacion": self.no_operacion,
                    #"rfc_emisor_cta_ord": str(factura.partner_id.nif),
                    "rfc_emisor_cta_ord": str(self.rfc_emisor_cta_ord),
                    "nom_banco_ord_ext_id": str(self.nom_banco_ord_ext_id.c_nombre),
                    "cta_ordenante": str(self.cta_ordenante),
                    "rfc_emisor_cta_ben": str(self.rfc_emisor_cta_ben),
                    "cta_beneficiario": str(self.cta_beneficiario),
                    "documentos": [
                        {
                            "id_documento": str(factura.uuid),
                            "serie": factura.fac_serie,
                            "folio": factura.fac_folio,
                            "moneda_dr": str(factura.currency_id.name),
                            "tipo_cambio_dr": str(self.tipocambio_oper),
                            "metodo_de_pago_dr": 'PPD',
                            "num_parcialidad": str(self.no_parcialidad),
                            "imp_pagado": str(self.imp_pagado),
                            "imp_saldo_ant": str(self.imp_saldo_ant),
                            "imp_saldo_insoluto": str(self.imp_saldo_insoluto)
                        }
                    ]
                }
            }
        }

        #Coloca datos de Receptor (no obligatorios)
        if factura.partner_id.state_id.name != None and factura.partner_id.state_id.name != False:
            data["factura"]["receptor"]["estado"] = factura.partner_id.state_id.name.encode('utf-8');

        if factura.partner_id.name != None and factura.partner_id.name != False:
            data["factura"]["receptor"]["compania"] = factura.partner_id.name.encode('utf-8');

        if factura.partner_id.city != None and factura.partner_id.city != False:
            data["factura"]["receptor"]["ciudad"] = factura.partner_id.city.encode('utf-8');

        if factura.partner_id.street != None and factura.partner_id.street != False:
            data["factura"]["receptor"]["calle"] = factura.partner_id.street.encode('utf-8');

        if factura.partner_id.zip != None and factura.partner_id.zip != False:
            data["factura"]["receptor"]["codigopostal"] = factura.partner_id.zip.encode('utf-8');

        if factura.partner_id.colonia != None and factura.partner_id.colonia != False:
            data["factura"]["receptor"]["colonia"] = factura.partner_id.colonia.encode('utf-8');

        if factura.partner_id.numero_ext != None and factura.partner_id.numero_ext != False:
            data["factura"]["receptor"]["numero_ext"] = factura.partner_id.numero_ext.encode('utf-8');



        #CFDIRelacionados (Para reemplazo de pagos)
        if self.sustituye_pago == True:
            cfdi_relacionados = []
            cfdi_relacionado = {
               "uuid": self.pago_sustituye.uuid
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
            self.timbrada = 'Timbrada'
            # En caso de recibir una respuesta positiva anexa el uuid al formulario de la factura timbrada
            self.uuid = json_data['result']['uuid']
            self.fac_id = json_data['result']['fac_id']
        else:
            raise ValidationError(json_data['result']['message'])

    @api.multi
    def cancelar_pagos_timbrada(self):

        self.cancel();

        url_parte = self.env['catalogos.configuracion'].search([('url', '!=', '')])
        url = str(url_parte.url)+"webresources/FacturacionWS/Cancelar"
        # print "1"
        data = {
          "uuid": self.uuid
        }

        headers = {
           'content-type': "application/json", 'Authorization':"Basic YWRtaW46YWRtaW4="
    }


        self._logger.info(json.dumps(data));
        response = requests.request("POST", url, data=json.dumps(data), headers=headers)
        self._logger.info(response.text );
        json_data = json.loads(response.text)
        if json_data['result']['success'] == 'true' or json_data['result']['success'] == True:
            self.timbrada = 'Pago Cancelado'
            self.state = "canceled";

        else:
            raise ValidationError(json_data['result']['message'])



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


    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted'), ('canceled', 'Cancelado'), ('replaced', 'Reemplazado')], string='Status',
      required=True, readonly=True, copy=False, default='draft',
      help='All manually created new journal entries are usually in the status \'Unposted\', '
           'but you can set the option to skip that status on the related journal. '
           'In that case, they will behave as journal entries automatically created by the '
           'system on document validation (invoices, bank statements...) and will be created '
           'in \'Posted\' status.')



    @api.one
    def Puede_Timbrar(self):
        #invoice = self.env['account.invoice'].browse(self._context.get('active_ids'))
        #self._logger.info(self.ref)
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

    @api.one
    def Puede_Editar(self):
        #if self.move_timbrada == 'Sin Timbrar' and self.state not in ['canceled','replaced']:
        if 'Sin Timbrar' in self.move_timbrada:
            self.move_puede_editar = True;
            return True;
        else:
            self.move_puede_editar = False;
            return False;

    move_puede_editar = fields.Boolean(string='Puede Editar',store=False,compute=Puede_Editar)


    @api.onchange('move_nom_banco_ord_ext_id')
    def _onchange_establecer_banco_emisor(self):
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
                    "receptor_id": factura.rfc_cliente_factura,
                    "NIF": factura.partner_id.nif,
                    "correo": factura.partner_id.email.encode('utf-8'),

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

        #Coloca datos de Receptor (no obligatorios)
        if factura.partner_id.state_id.name != None and factura.partner_id.state_id.name != False:
            data["factura"]["receptor"]["estado"] = factura.partner_id.state_id.name.encode('utf-8');

        if factura.partner_id.name != None and factura.partner_id.name != False:
            data["factura"]["receptor"]["compania"] = factura.partner_id.name.encode('utf-8');

        if factura.partner_id.city != None and factura.partner_id.city != False:
            data["factura"]["receptor"]["ciudad"] = factura.partner_id.city.encode('utf-8');

        if factura.partner_id.street != None and factura.partner_id.street != False:
            data["factura"]["receptor"]["calle"] = factura.partner_id.street.encode('utf-8');

        if factura.partner_id.zip != None and factura.partner_id.zip != False:
            data["factura"]["receptor"]["codigopostal"] = factura.partner_id.zip.encode('utf-8');

        if factura.partner_id.colonia != None and factura.partner_id.colonia != False:
            data["factura"]["receptor"]["colonia"] = factura.partner_id.colonia.encode('utf-8');

        if factura.partner_id.numero_ext != None and factura.partner_id.numero_ext != False:
            data["factura"]["receptor"]["numero_ext"] = factura.partner_id.numero_ext.encode('utf-8');



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
        else:
            raise ValidationError(json_data['result']['message'])

    @api.multi
    def cancelar_pagos_timbrada(self):

        #Busca el pago y lo coloca como cancelado
        # for move_line in self.line_ids:
        #     print "cancelar"
        #     move_line.payment_id.write({"state":"canceled"})

        movimiento_id = self.id;


        url_parte = self.env['catalogos.configuracion'].search([('url', '!=', '')])
        url = str(url_parte.url)+"webresources/FacturacionWS/Cancelar"
        # print "1"
        data = {
          "uuid": self.move_uuid
        }

        self.line_ids.remove_move_reconcile()
        self.button_cancel()
        self.state = "canceled";

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

