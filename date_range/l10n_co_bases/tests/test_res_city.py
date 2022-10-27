# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class TestResCity(TransactionCase):

    def test_name_search(self):
        """
        Check name_search on res_city
        """
        # Create a city
        city_id = self.env.ref('l10n_co_bases.state_co_201')

        # Check name_search
        ns_name = tuple(set(i[0] for i in self.env['res.city'].name_search('MEDELLÍ')))
        self.assertEqual(ns_name, (city_id.id,))
        