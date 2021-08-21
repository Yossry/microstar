import pdb

from odoo import _, fields, models, api
from odoo.exceptions import UserError, ValidationError


class SaleCommissionSalaryInput(models.TransientModel):
    _name = "sale.commission.salary.input"
    _description = "Sale Commission Salary Input"

    @api.model
    def _default_settlement_id(self):
        emp_id = self.env['sale.commission.settlement'].browse(self._context.get('active_id', False))
        return emp_id and emp_id.id or False

    settlement_id = fields.Many2one("sale.commission.settlement", domain="[('state', '=', 'settled'),('agent_type', '=', 'agent')]", default=_default_settlement_id)

    date = fields.Date(default=fields.Date.context_today)

    def action_create_salary_inputs(self):
        for rec in self:
            # lines creation in hr_salary_inputs
            input_obj = self.env['hr.emp.salary.inputs']
            rule_input_id = False
            rule_input_id = self.env['hr.salary.inputs'].search([('code', '=', 'COM')])
            if not rule_input_id:
                raise UserError('Please First Configure the Input Type for the Loans')
            code = 'COM'
            employee_id = self.env['hr.employee'].search([('agent_id', '=', self.settlement_id.agent_id.id)])
            input_id = input_obj.create({
                'employee_id': employee_id and employee_id.id or False,
                'name': code,
                'amount': self.settlement_id.total,
                'state': 'confirm',
                'input_id': rule_input_id and rule_input_id.id or False,
                'date': self.date,
            })
