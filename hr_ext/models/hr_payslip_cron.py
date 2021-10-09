from collections import defaultdict
from odoo.tools import date_utils
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class HRPayslipCron(models.Model):
    _name = 'hr.payslip.cron'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Payslip Cron Jobs'
    _order = 'id desc'

    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', 'Employee', tracking=True, required=True)
    code = fields.Char('Code')
    date_from = fields.Date("Date From", tracking=True)
    date_to = fields.Date("Date To", tracking=True)
    department_id = fields.Many2one('hr.department', 'Department')
    job_id = fields.Many2one('hr.job', 'Job')
    contract_id = fields.Many2one('hr.contract', 'Contract', tracking=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('generate', 'Generate'),
                              ('difference', 'Difference'),
                              ('done', 'Done'),
                              ('noc', 'No Contract'),
                              ('error', 'Error')
                              ], 'Status', readonly=True, default='draft', tracking=True)
    slip_id = fields.Many2one('hr.payslip', 'Payslip')
    note = fields.Text('Note', related='slip_id.note', tracking=True)

    @api.model
    def create(self, values):
        if values.get('employee_id', False):
            employee = self.env['hr.employee'].search([('id', '=', values['employee_id'])])
            dup_entry = self.env['hr.payslip.cron'].search([('employee_id', '=', values.get('employee_id')), ('date_from', '>=', values['date_from']), ('date_to', '<=', values['date_to'])])
            if dup_entry:
                raise UserError("Duplicate Entry Found For the Employee (%s) and Code (%s) and Cron ID (%s)" % (employee.name, employee.code, dup_entry.id))
        if not values.get('name', False):
            values['name'] = self.env['ir.sequence'].next_by_code('hr.payslip.cron')
        payslip_cron = super(HRPayslipCron, self).create(values)
        if not payslip_cron.name:
            payslip_cron.name = self.env['ir.sequence'].next_by_code('giki.paysrlip.cron')
        return payslip_cron

    @api.model
    def generate_slips(self, nlimit=100):
        Payslip = self.env['hr.payslip']
        cron_draft_slips = self.search([('state', '=', 'draft')], limit=nlimit)
        if cron_draft_slips:
            for cron_slip in cron_draft_slips:
                contracts = self.env['hr.contract'].search([('employee_id', '=', cron_slip.employee_id.id),
                                                            ('state', 'not in', ('close', 'cancel'))])
                if contracts:
                    contracts = contracts[0]
                else:
                    cron_slip.state = 'noc'
                    contracts = False
                _logger.info('.... cron called is called for slip generation .. %r..............', cron_slip.id)

                default_values = Payslip.default_get(Payslip.fields_get())
                for contract in contracts:
                    values = dict(default_values, **{
                        'employee_id': contract.employee_id.id,
                        'date_from': cron_slip.date_from,
                        'date_to': cron_slip.date_to,
                        'contract_id': contract.id,
                        'struct_id': contract.structure_type_id.default_struct_id.id,
                    })
                    payslip = self.env['hr.payslip'].new(values)
                    payslip._onchange_employee()
                    values = payslip._convert_to_write(payslip._cache)
                    new_slip = Payslip.create(values)
                    new_slip.compute_sheet()

                    cron_slip.write({'state': 'generate', 'slip_id': new_slip.id})
                    cron_slip.write({'state': 'generate'})
                    _logger.info('.... slip is generated .. %r..............', new_slip.id)
