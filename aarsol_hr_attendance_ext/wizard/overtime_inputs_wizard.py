import time
import pdb
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OverTimeInputsWizard(models.TransientModel):
    _name = 'overtime.inputs.wizard'
    _description = 'OverTime Inputs Wizard'

    @api.model
    def _get_employee_ids(self):
        emp_ids = self.env['hr.employee'].search([])
        return emp_ids and emp_ids.ids or []

    date_from = fields.Date('From Date', required=True, default=lambda *a: str(datetime.now() + relativedelta.relativedelta(day=1))[:10])
    date_to = fields.Date('To Date', required=True, default=lambda *a: str(datetime.now() + relativedelta.relativedelta(day=31))[:10])


    def overtime_to_inputs(self):
        recs = self.env['hr.employee.overtime'].search(
            [('overtime_status', '=', 'unpost'), ('state', '=', 'verify'),
             ('entry_date', '>=', self.date_from),
             ('entry_date', '<=', self.date_to)])

        employee_ids = recs.mapped('employee_id')
        for emp in employee_ids:
            overtimes = self.env['hr.employee.overtime'].search([('employee_id', '=', emp.id), ('state', '=', 'verify'), ('entry_date', '>=', self.date_from), ('entry_date', '<=', self.date_to)])
            if overtimes:
                ot_amt = 0
                total_hours = 0
                for ot in overtimes:
                    ot_amt += ot.amount
                    total_hours += ot.duration or 0.0
                res = {
                    'employee_id': emp.id,
                    'amount': ot_amt or 0,
                    'description': 'Overtime of Mr. ' + emp.name + ' For hours =' + str(total_hours) + ' And Amount=' + str(ot_amt) + '.',
                    'date': self.date_to,
                    'state': 'confirm',
                    'name': 'OT',
                    'over_time_hours': total_hours or 0.0,
                }
                rec_id = self.env['hr.salary.inputs'].sudo().create(res)
                overtimes.write({'overtime_status': 'post', 'input_id': rec_id.id})
