from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
import pdb

import logging

_logger = logging.getLogger(__name__)


class HRSalaryInputs(models.Model):
    _name = "hr.salary.inputs"
    _description = 'HR Salary Inputs'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    code = fields.Char('Code')
    input_type = fields.Selection([('alw', 'Allowance'),
                                   ('ded', 'Deduction')], 'Input Type')
    account_id = fields.Many2one('account.account', 'Account')
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Salary Rule')
    salary_structure_id = fields.Many2one('hr.payroll.structure', 'Salary Structure')  # General, Teaching

    payslip_input_type = fields.Many2one('hr.payslip.input.type', 'Payslip Input Type')
    note = fields.Text('Note')

    _sql_constraints = [
        ('code', 'unique(code)', "Code already exists "), ]

    @api.model
    def create(self, values):
        res = super(HRSalaryInputs, self).create(values)
        if res.code:
            line_data = {
                'name': res.name,
                'code': res.code,
                'struct_ids': [(4, res.salary_structure_id.id, None)],  # [(4, self.salary_structure_id.id, None)]
            }
            input_type = self.env['hr.payslip.input.type'].create(line_data)
            if input_type:
                res.payslip_input_type = input_type.id
            res.create_salary_input_rule()
        return res

    def write(self, vals):
        res = super(HRSalaryInputs, self).write(vals)
        for rec in self:
            if not rec.salary_rule_id and vals.get('code', False):
                rec.create_salary_input_rule()
        return res

    def unlink(self):
        for rec in self:
            if rec.salary_rule_id and rec.salary_rule_id.structure_ids:
                raise ValidationError(_('Salary Rule is linked with Payroll Structure'))
            rec.salary_rule_id.unlink()
        return super(HRSalaryInputs, self).unlink()

    def create_salary_input_rule(self):
        lines = []
        line_data = {
            'name': self.name,
            'code': self.code,
        }
        lines.append([0, 0, line_data])
        data = {
            'name': self.name,
            'code': self.code,
            'sequence': 90 if self.input_type=='alw' else 190,
            'quantity': 1,
            'category_id': 2 if self.input_type=='alw' else 4,  # 2. Allowance,  4. Deduction
            'active': True,
            'appears_on_payslip': True,
            'condition_select': 'python',
            'condition_python': "result = True if inputs.%s and inputs.%s.amount > 0 else False" % (self.code, self.code),
            'amount_select': 'code',
            'amount_python_compute': "result = inputs.%s.amount" % (self.code,) if self.input_type=='alw' else "result = -inputs.%s.amount" % (self.code,),
            'account_debit': self.account_id.id if self.input_type=='alw' else False,
            'account_credit': self.account_id.id if self.input_type=='ded' else False,
            'struct_id': self.salary_structure_id.id,
        }
        self.salary_rule_id = self.env['hr.salary.rule'].create(data).id

    def action_read_hr_salary_inputs(self):
        self.ensure_one()
        return {
            'name': "HR Salary Inputs Form",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.salary.inputs',
            'res_id': self.id,
        }


class HREmpSalaryInputs(models.Model):
    _name = "hr.emp.salary.inputs"
    _description = "Employee Salary Inputs"
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, tracking=True)
    amount = fields.Float(string='Amount', required=True)
    description = fields.Text('Description')
    date = fields.Date('Effecting Date', required=True, tracking=True)
    input_id = fields.Many2one('hr.salary.inputs', string='Category', required=True, tracking=True)
    name = fields.Char(related='input_id.code')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Paid'),
        ('cancel', 'Cancelled'), ], 'Status', default='draft', tracking=True)
    slip_id = fields.Many2one('hr.payslip', 'Pay Slip', ondelete='cascade', tracking=True)

    def inputs_validate(self):
        for rec in self:
            rec.write({'state': 'confirm'})

    def inputs_set_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def inputs_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def inputs_approve(self):
        for rec in self:
            rec.write({'state': 'confirm'})

    def unlink(self):
        for input_id in self:
            if input_id.state!='draft':
                raise ValidationError(_('You can only delete Salary Inputs in draft state .'))
        return super(HREmpSalaryInputs, self).unlink()

    def action_read_emp_salary_inputs(self):
        self.ensure_one()
        return {
            'name': "HR Employee Salary Inputs Form",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.emp.salary.inputs',
            'res_id': self.id,
        }
