from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import pdb


class HREmployeeMonthAttendanceVariations(models.Model):
    _name = "hr.employee.month.attendance.variations"
    _description = "Month Attendance Variations"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'

    name = fields.Char('Name', tracking=True)
    sequence = fields.Integer('Sequence')
    employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True, readonly=True, states={'draft': [('readonly', False)]})
    days = fields.Integer('Days', required=True, readonly=True, tracking=True, states={'draft': [('readonly', False)]})
    note = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], 'Status', tracking=True, default='draft')
    contract_id = fields.Many2one('hr.contract', "Contract", tracking=True)
    date = fields.Date('Date', tracking=True, default=fields.Date.today())

    def variation_confirm(self):
        self.state = 'done'

    def unlink(self):
        if not self.state=='draft':
            raise UserError(_('You Cannot Delete a Record that are not in Draft State'))
        return super(HREmployeeMonthAttendanceVariations, self).unlink()

    @api.model
    def create(self, values):
        res = super().create(values)
        if not res.name:
            res.name = self.env['ir.sequence'].next_by_code('hr.employee.month.attendance.variations')
        return res

    # @api.constrains('date')
    # def duplicate_constrains(self):
    #     for rec in self:
    #         if rec.date:
    #             first_day = rec.date.replace(day=1)
    #             last_day = rec.date + relativedelta(day=1, months=+1, days=-1)
    #             already_exist = self.env['hr.employee.month.attendance.variations'].search([('employee_id', '=', rec.employee_id.id),
    #                                                                                         ('date', '=>', first_day),
    #                                                                                         ('date', '<=', last_day),
    #                                                                                         ('id', '!=', rec.id)])
    #             if already_exist:
    #                 raise UserError(_('Employee %s Record already Exist for specified Date Period') % (rec.employee_id.name))
