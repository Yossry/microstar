from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError, AccessError
import pdb


class AccountAccount(models.Model):
    _inherit = 'account.account'
    _order = "code"


class AccountMove(models.Model):
    _inherit = 'account.move'

    voucher_type = fields.Selection([('BPV', 'BPV'),
                                     ('CPV', 'CPV'),
                                     ('BRV', 'BRV'),
                                     ('CRV', 'CRV'),
                                     ('JV', 'JV'),
                                     ('PV', 'PV'),
                                     ], string='Voucher Type')