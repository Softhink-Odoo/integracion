# -*- coding: utf-8 -*-
import urllib2
import webbrowser
import hashlib
import json
import ctypes
import os
import base64
import requests
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


#Agrega al formulario los capos requeridos por el Sat
class AccountInvoiceLine(models.Model):
    _name = 'account.invoice.line'
    _inherit = ['account.invoice.line']

    no_identificacion = fields.Char(string='No Identificador')

    @api.onchange('product_id')
    def _onchange_product(self):
        self.no_identificacion = self.product_id.default_code;
