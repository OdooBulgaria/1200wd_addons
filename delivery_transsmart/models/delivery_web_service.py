# -*- coding: utf-8 -*-
#
#    odoodev web_service.py
#    © 2016 December - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import requests
from requests.auth import HTTPBasicAuth
import json
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)
TRANS_API_ENDPOINTS = {
        'delivery.service.level': 'ServiceLevelOther',
        'delivery.service.level.time': 'ServiceLevelTime',
        'res.partner': 'Carrier',
        'transsmart.cost.center': 'Costcenter',
        'delivery.package.type': 'Package',}
TRANS_MODELS_LOCAL = [
        'delivery.service.level',
        'delivery.service.level.time',
        'res.partner',
        'transsmart.cost.center',
        'delivery.package.type',
        ]
TRANS_MODELS_VALS = {
        'delivery.service.level':{'code': 'Code',
            'name': 'Name',
            'transsmart_id': 'Id',
            },
        'delivery.service.level.time': {'code': 'Code',
            'name': 'Name',
            'transsmart_id': 'Id',
            },
        'res.partner': {'transsmart_code': 'Code',
            'name': 'Name',
            'supplier': True,
            'customer': False,
            'is_company': True,
            'transsmart_id': 'Id',
            'category_id': [(4, )],
            },
        'transsmart.cost.center': {'code': 'Code',
            'name': 'Name',
            'transsmart_id': 'Id',
            },
        'delivery.package.type': {'name': 'Name',
            'package_type': 'Type',
            'length': 'Length',
            'width': 'Width',
            'height': 'Height',
            'weight': 'Weight',
            'is_default': 'IsDefault',
            'transsmart_id': 'Id',
            },
        }


class DeliveryWebService(models.Model):
    _name = 'delivery.web.service'

    name = fields.Char(string="Title", required=True)
    url = fields.Char(string="URL", required=True, default="https://connect.test.api.transwise.eu/Api/")
    username = fields.Char(string="Username", required=True)
    password = fields.Char(string="Password", required=True)

    type = fields.Selection([('http_rest', 'HTTP REST')], 'Service Type', required=True)

    description = fields.Text()

    def send(self, method, params=None, payload=None):
        if self.type == 'http_rest':
            headers = {'content-type': 'application/json', 'charset': 'UTF-8'}

            response = requests.post(
                self.url + method,
                params=params,
                data=payload and json.dumps(payload) or None,
                headers=headers,
                verify=False,
                auth=HTTPBasicAuth(self.username, self.password))

            if response.status_code < 200 or response.status_code >= 300:
                _logger.error("HTTP ERROR {} - {}".format(response.status_code, response.text))
                if "Message" in response.text:
                    data = json.loads(response.text)
                    error_message = data["Message"]
                else:
                    error_message = "Transsmart communication error\n\n{}".format(response.text)
                raise Warning("ERROR {}: {}".format(response.status_code, error_message))

            return response.json()
        else:
            raise Warning('Transsmart connection error. Implementation for this web service type is missing: '
                          + self.type)

    def receive(self, method, params=None):
        if self.type == 'http_rest':
            headers = {'content-type': 'application/json'}

            response = requests.get(
                self.url + method,
                params=params,
                headers=headers,
                verify=False,
                auth=HTTPBasicAuth(self.username, self.password))

            if response.status_code < 200 or response.status_code >= 300:
                _logger.error("HTTP ERROR {} - {}".format(response.status_code, response.text))
                if "Message" in response.text:
                    data = json.loads(response.text)
                    error_message = data["Message"]
                else:
                    error_message = "Transsmart communication error\n\n{}".format(response.text)
                raise Warning("ERROR {}: {}".format(response.status_code, error_message))

            return response.json()
        else:
            raise Warning('Transsmart connection error. Implementation for this web service type is missing: '
                          + self.type)
