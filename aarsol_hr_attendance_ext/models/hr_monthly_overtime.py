from datetime import datetime, time
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
import pdb


class EmployeeMonthlyOvertime(models.Model):
    _name = "hr.employee.monthly.overtime"
    _description = "Employee Monthly OverTime"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    employee_code = fields.Char('Employee Code')
    department_id = fields.Many2one('hr.department', 'Department', readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Date', default=fields.Date.today(), required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    duration = fields.Float('Hours', required=False, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    minutes = fields.Integer('Minutes', required=False, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    amount = fields.Float(string='Total Amount', compute='get_total_amount', store=True, )
    month = fields.Char('Month', compute="_compute_month", store=True)
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('reject', 'Reject')
                              ], string='Status', default='draft', tracking=True)
    to_be_process = fields.Boolean('To Be Process', default=True)
    basic_pay = fields.Float('Basic Pay', compute='_compute_basic_pay', store=True)
    payroll_amount = fields.Float('Amount in Salary Slip', compute='_compute_extra_amount', store=True)
    extra_amount = fields.Float('Extra Amount', compute="_compute_extra_amount", store=True)
    salary_input_ref = fields.Char('Salary Input Ref')
    allow_previous_month = fields.Boolean('Allow Previous Month', default=False)
    is_previous_overtime = fields.Boolean('Is Previous Overtime', default=False)
    previous_month_date = fields.Date('Previous Overtime Date')

    def action_confirm(self):
        for rec in self:
            if rec.filtered(lambda ot: ot.state!='draft'):
                raise UserError(_('Overtime request must be in Draft State in order to Confirm it.'))

            # lines creation in hr_salary_inputs
            rule_input_id = self.env['ir.config_parameter'].sudo().get_param('aarsol_hr_attendance_ext.overtime_input_rule')
            if not rule_input_id:
                raise UserError('Please First Configure the Input Type for the Overtime')

            res = {
                'employee_id': rec.employee_id.id,
                'amount': rec.payroll_amount or 0,
                'date': rec.date,
                'state': 'confirm',
                'input_id': rule_input_id and int(rule_input_id) or False,
            }
            rec_id = self.env['hr.emp.salary.inputs'].sudo().create(res)
            rec.write({'state': 'confirm',
                       'month': datetime.strftime(rec.date, "%B-%Y"),
                       'salary_input_ref': rec_id.id})

    def action_refuse(self):
        for rec in self:
            rec.state = 'reject'
        return True

    def action_set_draft(self):
        for ot in self:
            ot.write({'state': 'draft'})
        return True

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.employee_code = rec.employee_id.code and rec.employee_id.code or ''
                rec.department_id = rec.employee_id.department_id and rec.employee_id.department_id.id or False

    @api.depends('employee_id')
    def _compute_basic_pay(self):
        for rec in self:
            basic_pay = 0
            contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id),
                                                          ('state', '=', 'open'),
                                                          ], order='id desc', limit=1)
            if not contract_id:
                contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id)
                                                              ], order='id desc', limit=1)
            if contract_id:
                basic_pay = contract_id.wage
            rec.basic_pay = basic_pay

    @api.depends('duration', 'minutes')
    def get_total_amount(self):
        for rec in self:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id),
                                                          ('state', '=', 'open'),
                                                          ], order='id desc', limit=1)
            if not contract_id:
                contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id)
                                                              ], order='id desc', limit=1)
            if contract_id:
                basic_wage = contract_id.wage
                if basic_wage > 0 and rec.date:
                    month_numbers = rec.date + relativedelta(day=31)
                    hours = month_numbers.day * 8
                    per_hour_salary = round(basic_wage / hours)
                    double_rate = round(per_hour_salary * 2)
                    rec.amount = (double_rate * rec.duration) + ((double_rate / 60) * rec.minutes)
                else:
                    rec.amount = 0
            else:
                rec.amount = 0

    @api.depends('amount')
    def _compute_extra_amount(self):
        for rec in self:
            config_apply_overtime_amount_limit = (self.env['ir.config_parameter'].sudo().get_param('aarsol_hr_attendance_ext.apply_overtime_amount_limit') or False)
            config_overtime_amount_limit = int(self.env['ir.config_parameter'].sudo().get_param('aarsol_hr_attendance_ext.overtime_amount_limit') or '3500')
            if config_apply_overtime_amount_limit:
                if config_overtime_amount_limit==0:
                    raise UserError(_('Overtime Limit Amount Should be Greater Zero.'))

                if not rec.allow_previous_month:
                    if rec.amount > config_overtime_amount_limit:
                        rec.extra_amount = rec.amount - config_overtime_amount_limit
                        rec.payroll_amount = config_overtime_amount_limit
                    else:
                        rec.extra_amount = 0
                        rec.payroll_amount = rec.amount

                if rec.allow_previous_month:
                    prev_month_entries = self.env['hr.employee.monthly.overtime'].search([('employee_id', '=', rec.employee_id.id),
                                                                                          ('month', '>=', rec.month),
                                                                                          ('state', '=', 'confirm'),
                                                                                          ('is_previous_overtime', '=', True),
                                                                                          ('id', '!=', rec._origin.id)])

                    if prev_month_entries:
                        prev_month_amount = 0
                        for prev_month_entry in prev_month_entries:
                            prev_month_amount += prev_month_entry.payroll_amount
                        if prev_month_amount > config_overtime_amount_limit:
                            rec.extra_amount = rec.amount
                            rec.payroll_amount = 0
                        elif prev_month_amount + rec.amount > config_overtime_amount_limit:
                            ot_amt = config_overtime_amount_limit - prev_month_amount
                            rec.payroll_amount = ot_amt
                            rec.extra_amount = rec.amount - ot_amt
                        else:
                            rec.extra_amount = 0
                            rec.payroll_amount = rec.amount
                    else:
                        if rec.amount > config_overtime_amount_limit:
                            rec.payroll_amount = config_overtime_amount_limit
                            rec.extra_amount = rec.amount - config_overtime_amount_limit
                        else:
                            rec.extra_amount = 0
                            rec.payroll_amount = rec.amount

            else:
                rec.extra_amount = 0
                rec.payroll_amount = rec.amount

    @api.model
    def create(self, values):
        """ Override to avoid automatic logging of creation """

        if not values.get('name', False):
            values['name'] = self.env['ir.sequence'].next_by_code('hr.employee.monthly.overtime')

        overtime = super(EmployeeMonthlyOvertime, self).create(values)
        if not overtime.month:
            if overtime.allow_previous_month and overtime.previous_month_date:
                overtime.month = datetime.strftime(overtime.previous_month_date, "%B-%Y")
            else:
                overtime.month = datetime.strftime(overtime.date, "%B-%Y")
        return overtime

    def unlink(self):
        for ot in self.filtered(lambda ot: ot.state not in ['draft', 'reject']):
            raise UserError(_('You cannot delete a Overtime which is in %s state.') % (ot.state,))
        return super(EmployeeMonthlyOvertime, self).unlink()

    @api.constrains('employee_id', 'date')
    def duplicate_constrains(self):
        for rec in self:
            if rec.employee_id and rec.date:
                if not rec.allow_previous_month:
                    duplicate_entry = self.env['hr.employee.monthly.overtime'].search([('employee_id', '=', rec.employee_id.id),
                                                                                       ('month', '=', rec.month),
                                                                                       ('id', '!=', rec._origin.id),
                                                                                       ('state', '!=', 'reject')])
                    if duplicate_entry:
                        raise UserError(_('Duplicate Entries are not Allowed, Please Contact your System Administrator'))

                if rec.allow_previous_month:
                    duplicate_entry = self.env['hr.employee.monthly.overtime'].search_count([('employee_id', '=', rec.employee_id.id),
                                                                                             ('month', '=', rec.month),
                                                                                             ('id', '!=', rec._origin.id),
                                                                                             ('state', '!=', 'reject')])
                    if duplicate_entry and duplicate_entry > 2:
                        raise UserError(_('Duplicate Entries are not Allowed, Please Contact your System Administrator'))

    @api.depends('date', 'previous_month_date', 'allow_previous_month')
    def _compute_month(self):
        for rec in self:
            if rec.allow_previous_month and rec.previous_month_date:
                rec.month = datetime.strftime(rec.previous_month_date, "%B-%Y")
            else:
                rec.month = datetime.strftime(rec.date, "%B-%Y")

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Overtime'),
            'template': '/aarsol_hr_attendance_ext/static/xls/overtime_template.xlsx'
        }]
