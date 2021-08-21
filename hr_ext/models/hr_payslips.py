from odoo import fields, models, api, _
from odoo.tools import date_utils
from odoo.tools.misc import format_date
import pdb
import logging

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    designation_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Designation', store=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department', store=True)

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []
        arrears_obj = self.env['hr.emp.salary.inputs']
        structures = contracts.structure_type_id.default_struct_id
        if structures and structures.input_line_type_ids:
            for rule_id in structures.input_line_type_ids:
                arr_amt = ''
                arr_ids = arrears_obj.search(
                    [('employee_id', '=', contracts.employee_id.id), ('name', '=', rule_id.code),
                     ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'confirm')])
                if arr_ids:
                    arr_amt = 0
                    for arr_id in arr_ids:
                        arr_amt += arr_id.amount
                inputs = {
                    'name': rule_id.name,
                    'code': rule_id.code,
                    'contract_id': contracts.id,
                    'amount': arr_amt or 0,
                    'input_type_id': rule_id.id,
                }
                res += [inputs]
        return res

    @api.model
    def get_inputs2(self, contracts, date_from, date_to):
        res = []
        rule_obj = self.env['hr.salary.rule']
        arrears_obj = self.env['hr.salary.inputs']
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        for contract in contracts:
            for rule in rule_obj.browse(sorted_rule_ids):
                if rule.input_ids:
                    for input in rule.input_ids:
                        arr_amt = ''
                        arr_ids = arrears_obj.search(
                            [('employee_id', '=', contract.employee_id.id), ('name', '=', input.code),
                             ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', 'confirm')])
                        if arr_ids:
                            arr_amt = 0
                            for arr_id in arr_ids:
                                arr_amt += arr_id.amount
                        inputs = {
                            'name': input.name,
                            'code': input.code,
                            'contract_id': contract.id,
                            'amount': arr_amt or 0,
                        }
                        res += [inputs]
        return res

    @api.model
    def get_contract(self, employee, date_from, date_to):
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', 'in', ('draft', 'open')), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id!=self.contract_id.employee_id:  # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        self.name = '%s - %s - %s' % (
            payslip_name, self.employee_id.name or '', format_date(self.env, self.date_from, date_format="MMMM y"))

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        else:
            self.warning_message = False
        # self.worked_days_line_ids = self._get_new_worked_days_lines()
        self.worked_days_line_ids = self._get_worked_day_lines_values_aarsol()
        if self.contract_id:
            self.input_line_ids = self._get_new_input_lines(self.contract_id, date_from, date_to)

    def _get_new_input_lines(self, contract, date_from, date_to):
        input_line_values = self.get_inputs(contract, date_from, date_to)
        if input_line_values:
            input_lines = self.input_line_ids.browse([])
            for r in input_line_values:
                input_lines |= input_lines.new(r)
            return input_lines
        else:
            return [(5, False, False)]

    # Get the total Days and Month Days from Custom Table Month Attendance
    def _get_worked_day_lines_values_aarsol(self):
        res = []
        total_leaves = 0
        attendance_days = 0
        # fill only if the contract as a working schedule linked
        self.ensure_one()

        max_work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', 'MAX')])
        # MAX Work Dict, it contains to month days
        attendance_line = {
            'sequence': 10,
            'work_entry_type_id': max_work_entry_type.id,
            'number_of_days': self.date_to.day,
            'number_of_hours': self.date_to.day * 8,
        }
        res.append(attendance_line)

        if self.contract_id and self.contract_id.date_start > self.date_from:
            attendance_days = (self.date_to - self.contract_id.date_start).days

        attendance_policy = self.env['ir.config_parameter'].sudo().get_param('hr_ext.attendance_policy')
        if attendance_policy=='bio':
            if attendance_days==0:
                attendance_recs = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id),
                                                                    ('check_in', '>=', self.date_from),
                                                                    ('check_out', '<=', self.date_to)])
                attendance_days = len(attendance_recs)

        if attendance_policy=='monthly':
            if attendance_days==0:
                employee_att_variation = self.env['hr.employee.month.attendance.variations'].search([('employee_id', '=', self.employee_id.id),
                                                                                                     ('date', '>=', self.date_from),
                                                                                                     ('date', '<=', self.date_to),
                                                                                                     ('state', '=', 'done')], order='id desc', limit=1)

                if employee_att_variation:
                    attendance_days = employee_att_variation.days

                if not employee_att_variation:
                    attendance_rec = self.env['hr.employee.month.attendance'].search([('employee_id', '=', self.employee_id.id),
                                                                                      ('date', '>=', self.date_from),
                                                                                      ('date', '<=', self.date_to),
                                                                                      ], order='id desc', limit=1)
                    if attendance_rec:
                        attendance_days = attendance_rec.present_days
                    else:
                        attendance_days = self.date_to.day

        work_entry_type = self.env['hr.work.entry.type'].search([('id', '=', 1)])
        if attendance_days > 0:
            attendance_line = {
                'sequence': 20,
                'work_entry_type_id': work_entry_type.id,
                'number_of_days': attendance_days,
                'number_of_hours': attendance_days * 8,
            }
            res.append(attendance_line)

        unpaid_time_off_recs = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                                            ('request_date_from', '>=', self.date_from),
                                                            ('request_date_to', '<=', self.date_to),
                                                            ('state', '=', 'validate'),
                                                            '|', ('holiday_status_id.name', '=', 'Unpaid'),
                                                            ('holiday_status_id.work_entry_type_id.name', '=', 'Unpaid')])
        if unpaid_time_off_recs:
            for unpaid_time_off_rec in unpaid_time_off_recs:
                total_leaves += unpaid_time_off_rec.number_of_days
                attendance_line = {
                    'sequence': 50,
                    'work_entry_type_id': unpaid_time_off_rec.work_entry_type_id.id,
                    'number_of_days': unpaid_time_off_rec.number_of_days,
                    'number_of_hours': unpaid_time_off_rec.number_of_days * 8,
                }
                res.append(attendance_line)

            # At res[1], there is the Working Days Attendance
            res[1]['number_of_days'] -= total_leaves
            res[1]['number_of_hours'] -= total_leaves * 8
        if res:
            worked_day_lines = self.worked_days_line_ids.browse([])
            for r in res:
                worked_day_lines |= worked_day_lines.new(r)
            return worked_day_lines
        return [(5, False, False)]

    def compute_sheet(self):
        for payslip in self.filtered(lambda slip: slip.state not in ['cancel', 'done']):
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()

            arr_ids = self.env['hr.emp.salary.inputs'].search(
                [('employee_id', '=', payslip.employee_id.id), ('date', '>=', payslip.date_from),
                 ('date', '<=', payslip.date_to), ('state', '=', 'confirm')])
            if arr_ids:
                loan_inputs = arr_ids.filtered(lambda z: z.input_id.code=='LOAN')
                if loan_inputs:
                    for loan_input in loan_inputs:
                        if loan_input.input_id.code=='LOAN':
                            a = 10
                            # loan_input.loan_line.paid = True
            arr_ids.write({'state': 'done', 'slip_id': payslip.id})

            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})

            # # For SMS
            # if not payslip.send_sms:
            #     slip_month = (tools.ustr(ttyme.strftime('%B-%Y')))
            #     text = "Dear Mr./Ms. " + payslip.employee_id.name + ", \n Your Salary For the Month of " + slip_month + " has been Generated. \n Regards, SOS."
            #     message = self.env['send_sms'].render_template(text, 'hr.payslip', payslip.id)
            #     mobile_no = (payslip.employee_id.mobile_phone and payslip.employee_id.mobile_phone) or (
            #             payslip.employee_id.work_phone and payslip.employee_id.work_phone) or False
            #     gatewayurl_id = self.env['gateway_setup'].search([('id', '=', 1)])
            # # if mobile_no:
            # #	self.env['send_sms'].send_sms_link(message, mobile_no, payslip.id, 'hr.payslip', gatewayurl_id)
        return True

    def action_payslip_done(self):
        if not self.env.context.get('without_compute_sheet'):
            self.compute_sheet()
            template = self.env.ref('aarsol_hr_ext.email_template_payslip')
            send = template.send_mail(self.id, force_send=True)
        return self.write({'state': 'done'})


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
            line.total = round(float(line.quantity) * line.amount * line.rate / 100)
