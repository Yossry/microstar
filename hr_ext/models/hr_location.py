from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError


class HRLocations(models.Model):
    _name = 'hr.location'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = 'Locations'

    name = fields.Char('Name', tracking=True)
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence')
    state = fields.Selection([('draft', 'Draft'),
                              ('lock', 'Locked')
                              ], string='Status', default='draft', tracking=True)
    remarks = fields.Text('Remarks')

    @api.constrains('name')
    def duplicate_constrains(self):
        for rec in self:
            already_exist = self.env['hr.location'].search([('name', '=', rec.name),
                                                            ('id', '!=', rec.id)])
            if already_exist:
                raise UserError(_('Duplicate Records are not Allowed.😀😀😀'))

    def action_lock(self):
        self.state = 'lock'

    def action_unlock(self):
        self.state = 'draft'

    def unlink(self):
        if not self.state=='draft':
            raise UserError(_('You can delete the Records that are in the Draft State.'))
        return super(HRLocations, self).unlink()
