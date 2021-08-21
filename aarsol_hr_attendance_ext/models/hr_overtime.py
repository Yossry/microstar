from datetime import datetime, timedelta, time
from pytz import timezone, utc
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
import pdb


def utcDate(self, ddate):
    user = self.env.user
    local_tz = timezone(user.tz)
    local_date = local_tz.localize(ddate, is_dst=False)
    utc_date = local_date.astimezone(utc)
    return utc_date


def localDate(self, utc_dt):
    user = self.env.user
    local_tz = timezone(user.tz)
    local_dt = utc_dt.replace(tzinfo=utc).astimezone(local_tz)
    return local_dt


def parse_date(td):
    resYear = float(td.days) / 365.0  # get the number of years including the the numbers after the dot
    resMonth = (resYear - int(resYear)) * 365.0 / 30.0  # get the number of months, by multiply the number after the dot by 364 and divide by 30.
    resDays = int((resMonth - int(resMonth)) * 30)
    resYear = int(resYear)
    resMonth = int(resMonth)
    return (resYear and (str(resYear) + "Y ") or "") + (resMonth and (str(resMonth) + "M ") or "") + (resMonth and (str(resDays) + "D") or "")


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day)


class HRAnalysisPeriod(models.Model):
    _name = 'hr.analysis.period'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "HR Analysis Period"

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence')
    period_from = fields.Date('Period From')
    period_to = fields.Date('Period To')
    month = fields.Integer('Month')
    month_abbr = fields.Char('Month Abbr')
    active_for_entry = fields.Boolean('Active')
    current = fields.Boolean('Current Year')


class HREmployeeOvertimeReason(models.Model):
    _name = "hr.employee.overtime.reason"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "OverTime Reasons"

    name = fields.Char('Name')
    code = fields.Char('Code')


class EmployeeOvertime(models.Model):
    _name = "hr.employee.overtime"
    _description = "Employee OverTime"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', readonly=True, states={'draft': [('readonly', False)]})
    entry_date = fields.Date('Entry Date', required=True, readonly=True, default=lambda self: str(datetime.now())[:10], states={'draft': [('readonly', False)]}, tracking=True)
    date = fields.Datetime('Duty Out Time', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True, help="Date on which this Overtime was performed.")
    duration = fields.Float('Hours', required=False, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    minutes = fields.Integer('Minutes', required=False, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    amount = fields.Float(string='Amount', readonly=True, store=True, compute='get_total_amount', states={'draft': [('readonly', False)]})
    month = fields.Char('Month', readonly=True, states={'draft': [('readonly', False)]})

    state = fields.Selection([('draft', 'Draft'),
                              ('verify', 'Verify'),
                              ('confirm', 'Confirm'),
                              ('reject', 'Reject')
                              ], 'State', default='draft', tracking=True, help='Select Type')
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    overtime_status = fields.Selection([('post', 'Paid'),
                                        ('unpost', 'UnPaid')
                                        ], 'Status', default='unpost', tracking=True)
    to_be_process = fields.Boolean('To Be Process', default=True)
    approve_date = fields.Date('Approve Date', readonly=True, tracking=True)
    verified_date = fields.Date('Verified Date', readonly=True, tracking=True)
    source = fields.Selection([('Single Entry', 'Single Entry'),
                               ('Multi Entry', 'Multi Entry')
                               ], default='Single Entry', string='Source')

    # @api.constrains('duration')
    # def _check_duration(self):
    #     for record in self:
    #         if record.duration > record.worked_hours:
    #             raise UserError(_("Please Check that Overtime Hours should be less than worked hours."))
    #     return True

    def action_overtime(self):
        domain = [[1, '=', 1]]
        abc = {
            'name': 'Employee Overtime',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'hr.employee.overtime',
            'views': [[False, 'list'], [False, 'form']],
            'domain': domain,
        }
        return abc

    def action_verify(self):
        for rec in self:
            if rec.filtered(lambda ot: ot.state!='draft'):
                raise UserError(_('Overtime request must be in Draft state ("To Submit") in order to Verify By Control Room it.'))
            rec.state = 'verify'
            rec.verified_date = str(datetime.today())

    def action_confirm(self):
        for rec in self:
            if rec.filtered(lambda ot: ot.state!='verify'):
                raise UserError(_('Overtime request must be in Verify state ("Control Room") in order to confirm it.'))
            rec.create_input_entry()
            rec.state = 'confirm'
            rec.month = datetime.strftime(rec.date, "%B-%Y")

    # def action_approve(self):
    # 	if self.filtered(lambda ot: ot.state != 'confirm'):
    # 		raise UserError(_('Overtime request must be in Confirm state, in order to Approve it.'))
    # 	for ot in self:
    # 		ot.state = 'approve'
    # 		ot.approve_date = str(datetime.today())

    # def action_validate(self):
    # 	for ot in self:
    # 		ot.state = 'verify'
    # 		ot.verified_date = str(datetime.today())
    # 		ot.create_input_entry()

    def action_refuse(self):
        for rec in self:
            rec.state = 'reject'
            rec.overtime_status = 'unpost'
        return True

    def action_status_unpost(self):
        for rec in self:
            if not rec.overtime_status=='unpost':
                rec.overtime_status = 'unpost'
        return True

    def action_status_post(self):
        for rec in self:
            if not rec.overtime_status=='post':
                rec.overtime_status = 'post'
        return True

    def action_set_draft(self):
        for ot in self:
            ot.write({'state': 'draft'})
        return True

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
                    # month_numbers = rec.date + relativedelta(day=31)
                    # hours = month_numbers.day * 8
                    # per_hour_salary = round(basic_wage / hours)
                    # double_rate = round(per_hour_salary * 2)
                    # rec.amount = (double_rate * rec.duration) + ((double_rate / 60) * rec.minutes)
                    rec.amount = round(((basic_wage * rec.duration) / 120), 0)
                else:
                    rec.amount = 0
            else:
                rec.amount = 0

    @api.model
    def process_OT(self, nlimit=100):
        recs = self.search([('to_be_process', '=', True)], limit=nlimit)
        for ot in recs:
            ot.input_id.amount = ot.input_id.amount - ot.amount
            if ot.input_id.slip_id:
                slip_ot_input_id = ot.input_id.slip_id.input_line_ids.filtered(lambda a: a.code=='OT')
                if slip_ot_input_id:
                    slip_ot_input_id.amount = slip_ot_input_id.amount - ot.amount
                    ot.input_id.slip_id.compute_sheet()
            ot.to_be_process = False

    @api.model
    def create(self, values):
        """ Override to avoid automatic logging of creation """
        if str(datetime.combine(fields.Date.from_string(values.get('date')), time.min) + timedelta(hours=+5))[:10] > str(datetime.now() + timedelta(days=+1, hours=+5))[:10]:
            raise UserError(_('You cannot Book in Advance the Overtime!'))

        if not values.get('name', False):
            values['name'] = self.env['ir.sequence'].next_by_code('hr.employee.overtime')

        overtime = super(EmployeeOvertime, self).create(values)
        if not overtime.month:
            overtime.month = datetime.strftime(overtime.date, "%B-%Y")
        return overtime

    def unlink(self):
        for ot in self.filtered(lambda ot: ot.state not in ['draft', 'reject']):
            raise UserError(_('You cannot delete a Overtime which is in %s state.') % (ot.state,))
        return super(EmployeeOvertime, self).unlink()
