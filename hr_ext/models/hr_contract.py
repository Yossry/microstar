from odoo import fields, models, api, SUPERUSER_ID, _
import pdb


class HRContract(models.Model):
    _inherit = 'hr.contract'

    mobile_allowances = fields.Monetary('Mobile Allowances')
    travelling_allowances = fields.Monetary('Travelling Allowances')
    laundry_allowances = fields.Monetary('Laundry Allowance')
    gross_salary = fields.Monetary('Gross Salary', compute='compute_gross_salary', store=True)

    @api.depends('wage', 'mobile_allowances', 'travelling_allowances', 'laundry_allowances')
    def compute_gross_salary(self):
        for rec in self:
            rec.gross_salary = rec.wage + rec.travelling_allowances + rec.mobile_allowances + rec.laundry_allowances

    @api.onchange('employee_id')
    def new_onchange_employee(self):
        if self.employee_id:
            contracts = self.search_count([('employee_id', '=', self.employee_id.id)])
            contracts += 1
            self.name = str(self.employee_id.name) + '-' + str(contracts)
