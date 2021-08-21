# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech(<https://www.iTech.com.eg>).                  #
#                                                                           #
#############################################################################

from odoo.exceptions import UserError
from odoo import models, fields, api, _
from odoo.http import request
import qrcode, base64
from io import BytesIO

class QRCodeAddon(models.Model):
    _inherit = 'account.move'

    def create_qr_code(self, url):
        qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4, )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_img = base64.b64encode(temp.getvalue())
        return qr_img

    qr_code_image = fields.Binary("QR Code", compute='_generate_qr_code')

    def _generate_qr_code(self):
        system_parameter_url = request.env['ir.config_parameter'].get_param('web.base.url')
        system_parameter_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        self.qr_code_image = self.create_qr_code(system_parameter_url)

