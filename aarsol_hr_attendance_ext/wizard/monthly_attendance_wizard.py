import pdb
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from odoo import tools
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MonthlyAttendanceWizard(models.TransientModel):
    _name = 'monthly.attendance.wizard'
    _description = 'Monthly Attendance Wizard'

    date = fields.Date('Date', required=True, default=lambda self: str(datetime.now() + relativedelta.relativedelta(months=-1, day=1))[:10])
    total_days = fields.Integer('Month Days', required=True, default=30)
    present_days = fields.Integer('Present Days', required=True, default=30)

    def mark_attendance(self):
        att_obj = self.env['hr.employee.month.attendance']
        employees = self.env['hr.employee'].search([])
        if employees:
            for emp in employees:
                # Checking Already Attendance of employee for this month ###
                if att_obj.search([('employee_id', '=', emp.id), ('date', '>=', self.date), ('date', '<=', self.date)]):
                    continue
                else:
                    res = {
                        'date': self.date,
                        'total_days': self.total_days,
                        'present_days': self.present_days,
                        'employee_id': emp.id,
                        'state': 'draft',
                    }
                    att_obj.create(res)
            return {'type': 'ir.actions.act_window_close'}
