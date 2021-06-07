# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ProductOrigin(models.Model):
    _name = "product.origin"
    _description = "Product Origin"
    _inherit = ['mail.thread']

    name = fields.Char('Name', required=True, tracking=True)
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True, tracking=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('lock', 'Locked')
                              ], string='Status', default='draft', tracking=True)

    _sql_constraints = [('name_unique', 'UNIQUE(name)', _('Name Duplicate!')), ]

    def action_lock(self):
        self.state = 'lock'

    def action_unlock(self):
        self.state = 'draft'

    def unlink(self):
        if not self.state=='draft':
            raise UserError(_('You can delete the Records that are in the Draft State.'))
        return super(ProductOrigin, self).unlink()
