# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openerp import fields, models, registry
from openerp.exceptions import Warning


_logger = logging.getLogger(__name__)


class BaseConnection(models.Model):
    _name = 'base.connection'

    name = fields.Char(string="Title", required=True)
    url = fields.Char(
        string="URL",
        required=True,
    )
    model = fields.Selection(
        selection=[
            ('echo', 'Echo Service'),
            ('test', 'Test Service'),
            ('http', 'HTTP Rest service'),
        ],
        string='Service type model',
        required=True,
    )
    description = fields.Text()

    def _handle_response(
            self, request_type, request_url, request_headers,
            response, params=None, payload=None):
        """Generic handling of get and post requests.

        returns warnings and errors and takes care of logging.
        """
        log_cr = registry(self.env.cr.dbname).cursor()
        log_model = self.env['http.request.log'].with_env(self.env(cr=log_cr))
        # use sudo() because it must always be possible to create a log
        log_line = log_model.sudo().create({
            'request_type': request_type,
            'request_url': request_url,
            'request_headers': str(request_headers),
            'request_params': params and str(params) or False,
            'request_payload': payload and json.dumps(payload) or False,
            'response_status_code': response.status_code,
            'response_data': response.text,
        })
        log_cr.commit()
        try:
            log_cr.close()
        except:
            _logger.warn("Could not close HHTP request logging cursor.")
        if not log_line:
            _logger.warn("Could not create HTTP Request log!")
        if response.status_code < 200 or response.status_code >= 300:
            _logger.error(
                "HTTP ERROR {} - {}".format(
                    response.status_code, response.text)
            )
            if "Message" in response.text:
                data = json.loads(response.text)
                error_message = data["Message"]
            else:
                error_message = \
                    "Transsmart communication error\n\n{}".format(
                        response.text
                    )
            raise Warning(
                "ERROR {}: {}".format(
                    response.status_code, error_message)
            )
        return response.json()

    def send(self, method, params=None, payload=None):
        request_headers = {
            'content-type': 'application/json',
            'charset': 'UTF-8',
        }
        request_url = self.url + method
        response = requests.post(
            request_url,
            params=params,
            data=payload and json.dumps(payload) or None,
            headers=request_headers,
            verify=False,
            auth=HTTPBasicAuth(self.username, self.password)
        )
        return self._handle_response(
            'post', request_url, request_headers,
            response, params=params, payload=payload
        )

    def receive(self, method, params=None):
        request_headers = {
            'content-type': 'application/json',
        }
        request_url = self.url + method
        response = requests.get(
            request_url,
            params=params,
            headers=request_headers,
            verify=False,
            auth=HTTPBasicAuth(self.username, self.password)
        )
        return self._handle_response(
            'post', request_url, request_headers,
            response, params=params, payload=None
        )