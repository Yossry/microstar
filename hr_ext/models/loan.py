import time
from datetime import datetime

from dateutil import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class HRLoans(models.Model):
    _name = 'hr.loans'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Loan Rule'

    name = fields.Char('Name', size=128, required=True)
    code = fields.Char('Code', size=64, required=True, )
    active = fields.Boolean('Active', help="If the active field is set to false, it will allow you to hide the Loan Rule without removing it.", default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    amount_max = fields.Float('Maximum Amount', required=True, )
    shares_max = fields.Float('Maximum Shares', required=True, )
    amount_percentage = fields.Float('(%) of Basic', required=True, help='Share amount of Loan per Payslip should be in the threshold value', default=30.0)
    note = fields.Text('Description')
    journal_id = fields.Many2one('account.journal', 'Loan Journal', required=True)
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Salary Rule')


class HRLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Business Loan"

    def _compute_quota(self):
        for rec in self:
            if rec.num_quotas > 0:
                rec.amount_quota = rec.amount / rec.num_quotas
            else:
                rec.amount_quota = 0

    @api.depends('amount', 'paid_amount', 'paid_quotas')
    def _compute_remaining(self):
        for rec in self:
            rec.remaining_debt = rec.amount - rec.paid_amount

    name = fields.Char("Name", tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    employee_code = fields.Char('Employee Code', related='employee_id.code', store=True)

    loan_id = fields.Many2one('hr.loans', 'Loan Category', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    amount = fields.Float('Loan Amount', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    amount_quota = fields.Float(compute='_compute_quota', string='Share Amount', store=False)
    num_quotas = fields.Integer('Number of shares to pay', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date('Start Date', readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    date_order = fields.Date('Date Order', readonly=True, states={'draft': [('readonly', False)]}, default=lambda *a: time.strftime('%Y-%m-%d'), tracking=True)
    date_payment = fields.Date('Date of Payment', readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    paid_quotas = fields.Integer('Shares paid', readonly=True, default=0)
    paid_amount = fields.Float('Paid Amount', readonly=True, default=0.0)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_amount')
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    remaining_debt = fields.Float(compute='_compute_remaining', string='Balance', store=True)
    active = fields.Boolean('Active', default=True)
    note = fields.Text('Note')
    state = fields.Selection([('draft', 'Draft'),
                              ('validate', 'Confirmed'),
                              ('paid', 'Paid')
                              ], string='State', default='draft')
    journal_id = fields.Many2one('account.journal', related='loan_id.journal_id', string="Loan Journal")
    debit_account_id = fields.Many2one('account.account', 'Debit Account', required=True, readonly=True)
    credit_account_id = fields.Many2one('account.account', 'Credit Account', required=True, readonly=True)
    code = fields.Char(related='loan_id.code', store=True, string="Code", tracking=True)
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True)
    payment_channel = fields.Selection([('bank', 'Bank'),
                                        ('cash', 'Cash')
                                        ], string='Payment Mode', default='bank')
    basic_pay = fields.Float('Basic Pay', compute='_compute_basic_pay', store=True, default=0)

    def _check_dates(self):
        current_date = datetime.now().strftime('%Y-%m-%d')
        for loan in self:
            if loan.date_start < current_date or loan.date_payment:
                return False
        return True

    @api.model
    def create(self, values):
        loans = self.env['hr.loans'].browse(values['loan_id'])
        employee = self.env['hr.employee'].browse(values['employee_id'])

        contract_id = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], order='id desc', limit=1)
        if not contract_id:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'draft')], order='id desc', limit=1)
        if not contract_id:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', employee.id)], order='id desc', limit=1)

        if not employee.contract_ids or not contract_id:
            raise UserError(_('This Employee have no Contract, Please Define its Contract First.'))

        if employee:
            if values['amount'] <= 0 or values['num_quotas'] <= 0:
                raise UserError('Amount of Loan and the number of Shares to pay should be Greater than Zero')

            if values['amount'] > loans.amount_max:
                raise UserError(_('Amount of Loan for (%s) is greater than Allowed amount for (%s)') % (employee.name, loans.name))

            if values['num_quotas'] > loans.shares_max:
                raise UserError(_('Number of Installments for (%s) is greater than Allowed Installments for (%s)') % (employee.name, loans.name))

            amount_quota = values['amount'] / values['num_quotas']
            if amount_quota > (contract_id.wage * (loans.amount_percentage / 100.0)):
                raise UserError(_('The requested Loan Amount for  (%s) Exceed the (%s)%% of his Basic Salary (%s). The Loan cannot be registered') % (employee.name, loans.amount_percentage, contract_id.wage))
            res = super(HRLoan, self).create(values)
            if not res.name:
                res.name = self.env['ir.sequence'].next_by_code('hr.loan')
        return res

    def write(self, values):
        if values.get('amount', False):
            if values['amount'] > self.loan_id.amount_max:
                raise UserError(_('Amount of Loan for (%s) is greater than Allowed amount for (%s)') % (self.employee_id.name, self.loan_id.name))

        if values.get('num_quotas', False):
            if values['num_quotas'] > self.loan_id.shares_max:
                raise UserError(_('Number of Installments for (%s) is greater than Allowed Installments for (%s)') % (self.employee_id.name, self.loan_id.name))

        if values.get('amount', False) and self.num_quotas > 0:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                          ('state', '=', 'open')
                                                          ], order='id desc', limit=1)
            amount_quota = values['amount'] / self.num_quotas
            if amount_quota > (contract_id.wage * (self.loan_id.amount_percentage / 100.0)):
                raise UserError(_('The requested Loan Amount for  (%s) Exceed the (%s)%% of his Basic Salary (%s). The Loan cannot be registered') % (self.employee_id.name, self.loan_id.amount_percentage, contract_id.wage))

        res = super(HRLoan, self).write(values)
        return res

    @api.depends('loan_line_ids.paid')
    def _compute_amount(self):
        total_paid_amount = 0.00
        for loan in self:
            for line in loan.loan_line_ids:
                if line.paid==True:
                    total_paid_amount += line.paid_amount

            balance_amount = loan.amount - total_paid_amount
            loan.total_amount = loan.amount
            loan.balance_amount = balance_amount
            loan.paid_amount = loan.amount - balance_amount

    def loan_confirm(self):
        for rec in self:
            rec.write({'state': 'validate'})

    def unlink(self):
        for rec in self:
            if rec.state!='draft':
                raise ValidationError(_('You can only delete Entries that are in draft state .'))
        return super(HRLoan, self).unlink()

    def loan_pay(self):
        # do accounting entries here
        move_pool = self.env['account.move']
        timenow = time.strftime('%Y-%m-%d')

        for loan in self:
            default_partner_id = loan.employee_id.address_home_id.id
            name = _('Loans To Mr. %s') % (loan.employee_id.name)
            move = {
                'narration': name,
                'date': timenow,
                'journal_id': loan.loan_id.journal_id.id,
            }

            amt = loan.amount
            partner_id = default_partner_id
            debit_account_id = loan.debit_account_id.id
            credit_account_id = loan.credit_account_id.id

            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0

            analytic_tags = self.env['account.analytic.tag']
            # analytic_tags += self.employee_id.analytic_tag_id
            # analytic_tags += self.employee_id.department_id.analytic_tag_id
            # analytic_tag_ids = [(6, 0, analytic_tags.ids)]

            if debit_account_id:
                debit_line = (0, 0, {
                    'name': loan.loan_id.name,
                    'date': timenow,
                    'partner_id': partner_id,
                    'account_id': debit_account_id,
                    'journal_id': loan.loan_id.journal_id.id or loan.journal_id.id,
                    'debit': amt > 0.0 and amt or 0.0,
                    'credit': amt < 0.0 and -amt or 0.0,
                    # 'analytic_tag_ids': analytic_tag_ids,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id and not loan.payment_channel=='cash':
                credit_line = (0, 0, {
                    'name': loan.loan_id.name,
                    'date': timenow,
                    'partner_id': partner_id,
                    'account_id': credit_account_id,
                    'journal_id': loan.loan_id.journal_id.id or loan.journal_id.id,
                    'debit': amt < 0.0 and -amt or 0.0,
                    'credit': amt > 0.0 and amt or 0.0,
                    # 'analytic_tag_ids': analytic_tag_ids,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if credit_account_id and loan.payment_channel=='cash':
                statement_rec = self.env['account.bank.statement'].search([('date', '=', loan.date_order), ('state', '=', 'open')])
                if statement_rec:
                    line_vals = ({
                        'statement_id': statement_rec.id,
                        'name': name,
                        'journal_id': 9,
                        'company_id': 1,
                        'date': loan.date_order,
                        'account_id': debit_account_id,
                        'entry_date': timenow,
                        'amount': -amt,
                    })
                    statement_line = self.env['account.bank.statement.line'].create(line_vals)

                    # Credit Entry
                    credit_line = (0, 0, {
                        'name': loan.loan_id.name,
                        'date': timenow,
                        'partner_id': partner_id,
                        'account_id': credit_account_id,
                        'journal_id': loan.loan_id.journal_id.id or loan.journal_id.id,
                        'debit': amt < 0.0 and -amt or 0.0,
                        'credit': amt > 0.0 and amt or 0.0,
                        # 'analytic_tag_ids': analytic_tag_ids,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

                else:
                    raise UserError(_('There is no CashBook entry Opened for this Date. May be Cashbook Validated.'))

            move.update({'line_ids': line_ids})
            move_id = move_pool.create(move)
            self.write({'move_id': move_id.id, 'state': 'paid'})
            # move_id.post()
            self.compute_loan_line()
        return True

    def compute_loan_line(self):
        loan_line = self.env['hr.loan.line']
        input_obj = self.env['hr.emp.salary.inputs']
        loan_line.search([('loan_id', '=', self.id)]).unlink()

        rule_input_id = False
        if self.loan_id.salary_rule_id:
            rule_input_id = self.env['hr.salary.inputs'].search([('salary_rule_id', '=', self.loan_id.salary_rule_id.id)])
        if not rule_input_id:
            raise UserError('Please First Configure the Input Type for the Loans')

        for loan in self:
            date_start_str = loan.date_payment
            counter = 1
            amount_per_time = loan.amount / loan.num_quotas
            for i in range(1, loan.num_quotas + 1):
                line_id = loan_line.create({
                    'paid_date': date_start_str,
                    'paid_amount': amount_per_time,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})

                # lines creation in hr_salary_inputs
                code = 'LOAN'
                input_id = input_obj.create({
                    'employee_id': loan.employee_id.id,
                    'name': code,
                    'amount': amount_per_time,
                    'state': 'confirm',
                    # 'loan_line' : line_id.id,
                    'input_id': rule_input_id and rule_input_id.id or False,
                    'date': date_start_str,
                })
                line_id.salary_input_id = input_id and input_id.id or False
                counter += 1
                date_start_str = date_start_str + relativedelta.relativedelta(months=+1)
        return True

    @api.depends('employee_id')
    def _compute_basic_pay(self):
        for rec in self:
            if rec.employee_id:
                contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id),
                                                              ('state', '=', 'open')], order='id desc', limit=1)
                if not contract_id:
                    contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id),
                                                                  ('state', '=', 'draft')], order='id desc', limit=1)
                if contract_id:
                    rec.basic_pay = contract_id.wage
                else:
                    rec.basic_pay = 0
            else:
                rec.basic_pay = 0


class HRLoanLine(models.Model):
    _name = "hr.loan.line"
    _description = "HR Loan Request Line"

    paid_date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    paid_amount = fields.Float(string="Paid Amount", required=True)
    paid = fields.Boolean(string="Paid")
    notes = fields.Text(string="Notes")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", ondelete='cascade')
    payroll_id = fields.Many2one('hr.payslip', string="Payslip Ref.")
    salary_input_id = fields.Many2one('hr.emp.salary.inputs', 'Salary Input Ref.')
    to_be = fields.Boolean(string='To Be', default=False)


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    loan_ids = fields.One2many('hr.loan', 'employee_id', 'Employee Loans')
