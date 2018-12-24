odoo.define('autofactura.pos_autofactura', function (require) {
"use strict";

var module = require('point_of_sale.models');
var core = require('web.core');
var gui = require('point_of_sale.gui');
var screens = require('point_of_sale.screens');
var _t = core._t;
var QWeb = core.qweb;

    screens.ReceiptScreenWidget.include({
        render_receipt: function() {
            var order = this.pos.get_order();
            order.reference_number = order.name.replace(_t("Order "), "");
            var url_autofactura = window.location.protocol+'//'+window.location.hostname+(window.location.port ? ':'+window.location.port: '');
            url_autofactura = url_autofactura+"/autofactura/autofactura";
            order.url_autofactura = url_autofactura;
            this.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                    widget:this,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines(),
                }));
        }
    });


    var _super_order = module.Order.prototype;
    module.Order = module.Order.extend({
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.reference_number = json.name.replace(_t("Order "), "");
            json.url_autofactura = window.location.href;
            //_t("Order ")
            _super_order.export_as_JSON.apply(this,arguments);

            _super_order

            return json;
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            //this.reference_number = json.uid.replace(/-/g, '');
            json.reference_number = json.name.replace(_t("Order "), "");
            //_t("Order ")
            console.log(json);
        }
    });
});

