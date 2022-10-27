import logging
import uuid
import math
import requests
import pprint
import time
import random

from hashlib import md5
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare
from odoo.tools.float_utils import float_repr

SUPPORTED_CURRENCIES = ('COP',)


_logger = logging.getLogger(__name__)


class PaymentAcquirerWompicol(models.Model):
    _inherit = 'payment.acquirer'

    # This fields are what's needed to configure the payment acquirer
    # These are extensions, there is a field state, which can be 'enabled'
    # 'test' or 'disabled' in this case, 'enabled' is 'prod'.
    provider = fields.Selection(selection_add=[('wompicol', 'Wompi Colombia')], ondelete={'wompicol': 'set default'})
    wompicol_private_key = fields.Char(
            string="Wompi Colombia Private API Key",
            required_if_provider='wompicol',
            groups='base.group_user'
            )
    wompicol_public_key = fields.Char(
            string="Wompi Colombia Public API Key",
            required_if_provider='wompicol',
            groups='base.group_user'
            )
    wompicol_test_private_key = fields.Char(
            string="Wompi Colombia Test Private API Key",
            required_if_provider='wompicol',
            groups='base.group_user'
            )
    wompicol_test_public_key = fields.Char(
            string="Wompi Colombia Test Public API Key",
            required_if_provider='wompicol',
            groups='base.group_user'
            )
    wompicol_event_url = fields.Char(
            string="Wompi Colombia URL de Eventos",
            required_if_provider='wompicol',
            groups='base.group_user',
            readonly=True,
            store=False,
            compute='_wompicol_event_url'
            )
    wompicol_test_event_url = fields.Char(
            string="Wompi Colombia URL Test de Eventos",
            required_if_provider='wompicol',
            groups='base.group_user',
            readonly=True,
            store=False,
            compute='_wompicol_event_url'
            )

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        """ Override of payment to unlist PayU Latam acquirers for unsupported currencies. """
        acquirers = super()._get_compatible_acquirers(*args, currency_id=currency_id, **kwargs)

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            acquirers = acquirers.filtered(lambda a: a.provider != 'wompicol')

        return acquirers

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'wompicol':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_wompicol.account_payment_method_wompicol').id

    def _wompicol_event_url(self):
        """Set the urls to config in the wompi console"""
        prod_url = ''
        test_url = ''
        if self.provider == 'wompicol':
            base_url = self.env[
                    'ir.config_parameter'
                    ].sudo().get_param('web.base.url')
            prod_url = f"{base_url}/payment/wompicol/response"
            test_url = f"{base_url}/payment/wompicol_test/response"

        self.wompicol_event_url = prod_url
        self.wompicol_test_event_url = test_url

    def _get_wompicol_api_url(self, environment=None):
        """This method should be called to get the api
        url to query depending on the environment."""
        if not environment:
            environment = 'prod' if self.state == 'enabled' else 'test'

        if environment == 'prod':
            return 'https://production.wompi.co/v1/'
        else:
            return 'https://sandbox.wompi.co/v1/'

    def _get_wompicol_urls(self):
        """ Wompi Colombia URLs this method should be called to
        get the url to GET the form"""
        return "https://checkout.wompi.co/p/"

    def _get_keys(self, environment=None):
        """Wompi keys change wether is prod or test
        returns a tuple with (pub, prod) dending on
        environment return the appropiate key."""
        if not environment:
            environment = 'prod' if self.state == 'enabled' else 'test'

        if environment == 'prod':
            prv = self.wompicol_private_key
            pub = self.wompicol_public_key
            return(prv, pub)
        else:
            test_prv = self.wompicol_test_private_key
            test_pub = self.wompicol_test_public_key
            return(test_prv, test_pub)


class PaymentTransactionWompiCol(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Payulatam-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """

        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'wompicol':
            return res
        base_url = self.env[
            'ir.config_parameter'
        ].sudo().get_param('web.base.url')
        api_url = self.acquirer_id._get_wompicol_urls()
        wompiref = f"{self.reference}"
        wompi_values = {
            'publickey': self.acquirer_id._get_keys()[1],
            'currency': 'COP',
            'amountcents': math.ceil(processing_values['amount']) * 100,
            'referenceCode': wompiref,
            'redirectUrl': urls.url_join(base_url, '/payment/wompicol/client_return'),
            'api_url': api_url,
        }
        return wompi_values

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on wompi data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        :raise: ValidationError if the signature can not be verified
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'wompicol':
            return tx

        ref = data['data']['transaction']['reference']

        tx = self.env[
            'payment.transaction'
        ].search([('reference', '=', ref)])

        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on Payulatam data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        """
        super()._process_feedback_data(data)
        if self.provider != 'wompicol':
            return

        self.acquirer_reference = data['data']['transaction'].get('id')

        status = data['data']['transaction'].get('status')
        state_message = data['data']['transaction'].get('status_message')
        if status == 'PENDING':
            self._set_pending(state_message=state_message)
        elif status == 'APPROVED':
            self._set_done(state_message=state_message)
        elif status in ('VOIDED', 'DECLINED', 'ERROR'):
            self._set_canceled(state_message=state_message)
        else:
            _logger.warning(
                "Estado de pago no reconocido %s para la transacción con referencia %s",
                status, self.reference
            )
            self._set_error("WompiCol: " + _("Invalid payment status."))


    def _wompicol_get_data_manually(self, id, environment):
        """When the client has returned and the payment transaction hasn't been
        updated, check manually and update the transaction"""
        # Check first if this transaciont has been updated already
        if id:
            tx = self.env[
                    'payment.transaction'
                    ].search([('acquirer_reference', '=', id)])
            if len(tx):
                _logger.info("Wompicol: Not getting data manually, transaction already updated.")
                return

        api_url = self.acquirer_id._get_wompicol_api_url(environment)
        request_url = f"{api_url}/transactions/{id}"
        wompi_data = requests.get(request_url, timeout=60)
        # If request succesful
        if wompi_data.status_code == 200:
            wompi_data = wompi_data.json()
            _logger.info("Wompicol: Sucesfully called api for id: %s it returned data: %s"
                         % (id, pprint.pformat(wompi_data)))
            # pprint.pformat(post))
            # Data needed to validate is just on 'data'
            # Format it how it expects it
            wompi_data["data"] = {"transaction": wompi_data["data"]}
            # Fix the reference code, only what's previous to _ is what we want
            ref = wompi_data['data']['transaction']['reference']

            wompi_data["noconfirm"] = True
            # If the transaction is a test.
            if environment == 'test':
                wompi_data["test"] = True
            _logger.info("Wompicol: creating transaction manually, by calling the api for acquirer reference %s" % id)
            self.env['payment.transaction'].sudo()._handle_feedback_data('wompicol', wompi_data)

