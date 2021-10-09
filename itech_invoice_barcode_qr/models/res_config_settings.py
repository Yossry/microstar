# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#    iTech Co.                                                              #
#                                                                           #
#    Copyright (C) 2020-iTech Technologies(<https://www.iTech.com.eg>).     #
#                                                                           #
#############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    print_barcode = fields.Boolean(default=True)
    print_qr = fields.Boolean(default=True)


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    print_barcode = fields.Boolean('Print Barcode', related="company_id.print_barcode", readonly=False,
                                   help="""If ticked, you can print the barcode in account invoice""",
                                   config_parameter='itech_invoice_barcode_qr.print_barcode')
    print_qr = fields.Boolean('Print QR Code', related="company_id.print_qr", readonly=False,
                              help="""If ticked, you can print the invoice URL as QR Code in account invoice""",
                              config_parameter='itech_invoice_barcode_qr.print_qr')