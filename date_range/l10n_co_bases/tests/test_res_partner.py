# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class TestPartner(TransactionCase):

    def test_name_search(self):
        """ Check name_search on partner, especially with domain based on auto_join
        user_ids field. Check specific SQL of name_search correctly handle joined tables. """
        values = {
            'name': 'Vlad the Impaler',
            'email': 'asd@gmail.com',
            'country_id': self.env.ref('base.co').id,
            'vat': '123456789',
            'vat_vd': '0',
        }
        test_partner = self.env['res.partner'].create(values)
        ns_name = tuple(set(i[0] for i in self.env['res.partner'].name_search('Vlad')))
        ns_vat = tuple(set(i[0] for i in self.env['res.partner'].name_search('1234567')))
        
        self.assertEqual(test_partner.id, ns_name[0])
        self.assertEqual(test_partner.id, ns_vat[0])


    def test_person_name(self):
        """
        Check person_name on partner
        """
        values = {
            'first_name': 'Juan',
            'middle_name': 'Alberto',
            'last_name': 'Gomez',
            'second_last_name': 'Mendoza',
            'email': 'asd@gmail.com',
            'country_id': self.env.ref('base.co').id,
            'vat': '123456789',
            'vat_vd': '0',
        }
        test_partner = self.env['res.partner'].person_name(values)
        self.assertEqual(test_partner['name'], 'Juan Alberto Gomez Mendoza')

    def test_check_unique_constraint(self):
        """
        Ensure you cant create two partners with the same vat
        """
        values = {
            'first_name': 'Juan',
            'middle_name': 'Alberto',
            'last_name': 'Gomez',
            'second_last_name': 'Mendoza',
            'email': 'asd@gmail.com',
            'country_id': self.env.ref('base.co').id,
            'vat': '123456789',
            'vat_vd': '0',
            'vat_type': '13',
        }
        test_partner = self.env['res.partner'].create(values)

        values = {
            'first_name': 'Juan',
            'middle_name': 'Alberto',
            'last_name': 'Gomez',
            'second_last_name': 'Mendoza',
            'email': 'asd@gmail.com',
            'country_id': self.env.ref('base.co').id,
            'vat': '123456789',
            'vat_vd': '0',
            'vat_type': '13',
        }

        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['res.partner'].create(values)

    def test_compute_vat_vd(self):
        """
        Check compute vat vd on partner
        """
        vat = '900088915'
        vat_vd = self.env['res.partner'].compute_vat_vd(vat)
        self.assertEqual(vat_vd, '7')

    def test_check_vat_vd(self):
        """
        Check check vat vd on partner
        """
        values = {
            'first_name': 'Juan',
            'middle_name': 'Alberto',
            'last_name': 'Gomez',
            'second_last_name': 'Mendoza',
            'email': 'asd@gmail.com',
            'country_id': self.env.ref('base.co').id,
            'vat': '900088915',
            'vat_vd': '1',
            'vat_type': '31',
        }
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['res.partner'].create(values)