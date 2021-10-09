import pdb
import time
from datetime import datetime, timedelta
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AttendanceActionReason(models.Model):
	_name = "attendance.action.reason"
	_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
	_description = "Action Reason"
	
	name = fields.Char('Reason', size=64, required=True, help='Specify the reason.')


class HREmployeeMonthAttendance(models.Model):
	_name = "hr.employee.month.attendance"
	_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
	_description = "Month Attendance"
	_order = 'id desc'

	date = fields.Date('Date', required=True,default=lambda *a: str(datetime.now() + relativedelta.relativedelta(day=1))[:10], tracking=True)
	employee_id = fields.Many2one('hr.employee', "Employee", required=True, tracking=True)
	state = fields.Selection([('draft','Draft'), ('counted', 'Counted'), ('done', 'Done')], 'Status', default='draft', tracking=True)
	total_days = fields.Integer('Month Days', required=True, default=30, tracking=True)
	present_days = fields.Integer('Present Days', required=True, default=30, tracking=True)
	total_hours = fields.Integer('Total Hours')
	present_hours = fields.Integer('Present Hours')
	overtime_hours = fields.Integer('Overtime Hours')
	#slip_id = fields.Many2one('hr.payslip', "Pay Slip")
	company_id = fields.Many2one('res.company','Company', related='employee_id.company_id', store=True)
	contract_id = fields.Many2one('hr.contract', "Contract", tracking=True)

	_sql_constraints = [
		('attendance_uniq', 'unique(date, employee_id,contract_id)', 'Attendance Date from Employee must be unique!'),
	]

	def unlink(self):
		for rec in self:		
			if rec.state == 'done':
				raise UserError('You can not delete attendance of Employess for which Salary have been Finalized.')
		return super(HREmployeeMonthAttendance, self).unlink()

	def attendance_confirm(self):
		for rec in self:
			if rec.state == 'draft':
				rec.state = 'done'
				
	def daily_to_month(self, period_id):
		employee_ids = self.env['hr.employee']
		period = self.env['hr.payroll.period'].browse(period_id)
		employee_ids |= self.env['hr.attendance'].search([('check_in','>=',period.date_start),('check_in','<=',period.date_end)]).mapped('employee_id')			
		
		for employee in self.env['hr.employee'].search([]):
			if 'AEX' in employee.category_ids.mapped('name'):		
				employee_ids |= employee
		
		for employee in employee_ids:
			present_days = 30
			contract_id = False
			
			variation_ids = self.env['hr.employee.month.attendance.variations'].search([('period_id', '=', period.id),('employee_id', '=', employee.id),])
			
			if variation_ids:
				for variation_id in variation_ids:
					present_days = variation_id.days
					if variation_id.contract_id:
						contract_id = variation_id.contract_id and variation_id.contract_id.id or False

					if present_days > 0:
						rec = {
							'date': period.date_end,
							'employee_id': employee.id,
							'present_days': present_days,
							'contract_id': contract_id or False,
						}
						self.create(rec)
			
			if not variation_ids:
				if present_days > 0:
					rec = {
						'date': period.date_end,
						'employee_id': employee.id,
						'present_days': present_days,
						'contract_id' : contract_id or False,
					}
					self.create(rec)

	def action_counted(self):
		for rec in self:
			rec.write({'state': 'counted'})


class HREmployee(models.Model):
	_inherit = 'hr.employee'

	def _attendance_count(self):
		# self.attendance_count = self.env['cit.attendance'].search_count([('employee_id', '=', self.id),('slip_id', '=', False)])
		self.attendance_count = 0

	def _month_attendance_count(self):
		for emp in self:
			month_total_days = month_att_days = 0
			att_recs = self.env['hr.employee.month.attendance'].search([('employee_id', '=', emp.id),('state','=','draft'),('slip_id','=',False)])
			for att_rec in att_recs:
				month_total_days += att_rec.total_days
				month_att_days += att_rec.present_days

			emp.month_total_days = month_total_days
			emp.month_att_days = month_att_days

	attendance_count = fields.Integer('Attendances', compute='_attendance_count')
	month_total_days = fields.Integer('Month Days', compute='_month_attendance_count')
	month_att_days = fields.Integer('Present Days', compute='_month_attendance_count')
	

