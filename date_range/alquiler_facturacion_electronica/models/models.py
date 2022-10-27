# -*- coding: utf-8 -*-

import base64
from webbrowser import open_new, open_new_tab

import math
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round, float_compare
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import xml.etree.ElementTree as ET
import os
import requests
import zipfile
from datetime import datetime, date
import re
import os
import glob
import functools
import operator


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_price_unit_inv_line(self, line):
        if float_compare(line.quantity, 1, precision_rounding=line.product_uom_id.rounding) == -1 and all(
                [sale_line.is_rental for sale_line in line.sale_line_ids]):
            line_price_unit = float_round(line.price_subtotal, precision_rounding=line.move_id.currency_id.rounding)
        else:
            line_price_unit = float_round((line.price_subtotal / (1 - (line.discount / 100))) / line.quantity,
                                          precision_rounding=line.move_id.currency_id.rounding)
        return line_price_unit

    def get_line_quantity(self, line):
        if float_compare(line.quantity, 1, precision_rounding=line.product_uom_id.rounding) == -1 and all(
                [sale_line.is_rental for sale_line in line.sale_line_ids]):
            line_quantity = line.quantity
        else:
            line_quantity = line.quantity
        return line_quantity



