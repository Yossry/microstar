import time
from datetime import datetime
from dateutil import relativedelta
import pdb
from odoo import api, fields, models


class PayslipsCronWizard(models.TransientModel):
    _name = 'payslips.cron.wizard'
    _description = 'Generate Cron Entries'

    date_from = fields.Date("Date From", default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=-1, day=1))[:10])
    date_to = fields.Date("Date To", default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=-1, day=31))[:10])
    department_ids = fields.Many2many('hr.department', 'payslip_cron_department_rel', 'wiz_id', 'dept_id', 'Departments')
    employee_ids = fields.Many2many('hr.employee', 'payslip_cron_employee_rel', 'cron_id', 'emp_id', string='Filter on Employees', help="Only selected Employees Salaries will be generated.")

    def generate_cron_entry(self):
        cron_slip_pool = self.env['hr.payslip.cron']
        emp_pool = self.env['hr.employee']
        att_ids = True

        for data in self:
            emp_domain = []
            if data.department_ids:
                emp_domain.append(('department_id', 'in', data.department_ids.ids))
            if data.employee_ids:
                emp_domain.append(('id', 'in', data.employee_ids.ids))

            emp_ids = emp_pool.search(emp_domain)
            for emp in emp_ids:
                payroll_attendance_type = self.env['ir.config_parameter'].sudo().get_param('aarsol_hr_ext.payroll_attendance_type')
                if payroll_attendance_type=='bio':
                    att_ids = self.env['hr.attendance'].search([('employee_id', '=', emp.id),
                                                                ('check_in', '>=', data.date_from),
                                                                ('check_out', '<=', data.date_to)])
                if payroll_attendance_type=='monthly':
                    att_ids = self.env['hr.employee.month.attendance'].search([('date', '>=', data.date_from),
                                                                               ('date', '<=', data.date_to),
                                                                               ('employee_id', '=', emp.id)])
                if payroll_attendance_type=='variation':
                    att_id = self.env['hr.employee.month.attendance.variations'].search([('date', '>=', data.date_from),
                                                                                         ('date', '<=', data.date_to),
                                                                                         ('employee_id', '=', emp.id),
                                                                                         ], order='id desc', limit=1)
                    if att_id and att_id.days==0:
                        att_ids = False

                if att_ids:
                    contract = False
                    # att_ids.write({'state': 'counted'})
                    contract = self.env['hr.contract'].search([('employee_id', '=', emp.id),
                                                               ('state', '=', 'open')], order='id desc', limit=1)
                    if not contract:
                        contract = self.env['hr.contract'].search([('employee_id', '=', emp.id)], order="id desc", limit=1)
                    res = {
                        'code': emp.code,
                        'employee_id': emp.id,
                        'date_from': data.date_from,
                        'date_to': data.date_to,
                        'department_id': emp.department_id and emp.department_id.id or False,
                        'job_id': emp.job_id and emp.job_id.id or False,
                        'contract_id': contract[0].id if contract else False,
                        'state': 'draft',
                    }
                    cron_rec = cron_slip_pool.create(res)
        return {'type': 'ir.actions.act_window_close'}
