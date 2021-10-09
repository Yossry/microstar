import pdb
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import math
import logging

_logger = logging.getLogger(__name__)


class HRStaffAdvance(models.Model):
    _name = 'hr.staff.advance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Advances To Staff"

    name = fields.Char("Description", required=True, readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    date = fields.Date('Date', readonly=True, states={'draft': [('readonly', False)]}, default=lambda *a: time.strftime('%Y-%m-%d'), tracking=True)
    payment_date = fields.Date('Payment Date', readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    paid_amount = fields.Float('Paid Amount', readonly=True, default=0.0, tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Confirmed'), ('paid', 'Paid')], string='State', default='draft', tracking=True)
    journal_id = fields.Many2one('account.journal', 'Loan Journal', required=True)
    debit_account_id = fields.Many2one('account.account', 'Debit Account', required=True, readonly=True)
    credit_account_id = fields.Many2one('account.account', 'Credit Account', required=True, readonly=True)
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True)
    payment_channel = fields.Selection([('bank', 'Bank'), ('cash', 'Cash')], string='Payment Mode', default='bank', tracking=True)
    check_number = fields.Char("Check Number")
    note = fields.Text('Note')

    def unlink(self):
        for rec in self:
            if rec.state!='draft':
                raise ValidationError(_('You can only delete Entries that are in draft state .'))
        return super(HRStaffAdvance, self).unlink()

    def advance_confirm(self):
        for advance in self:
            advance.state = 'validate'

    def advance_pay(self):
        # if Advance is Being Paid by the Cash then Cash is deducted from the Petty Cash, system do it auto,
        # if Advance is Paid by the Bank the Accounting Entries are Done. OtherWise no Entry.

        # do accounting entries here
        move_pool = self.env['account.move']
        timenow = time.strftime('%Y-%m-%d')
        input_obj = self.env['hr.emp.salary.inputs']

        rule_input_id = self.env['ir.config_parameter'].sudo().get_param('hr_ext.advance_input_rule')
        if not rule_input_id:
            raise UserError('Please First Configure the Input Type for the Advances')

        for advance in self:
            code = 'ADV'

            # Create Entry in hr_salary_inputs
            input_id = input_obj.create({
                'employee_id': advance.employee_id.id,
                'name': code,
                'amount': advance.paid_amount,
                'state': 'confirm',
                'input_id': rule_input_id,
                'date': advance.payment_date or time.strftime('%Y-%m-%d')
            })

            # Makeup of Move Data
            default_partner_id = advance.employee_id.address_home_id.id
            name = _('Advance To Mr. %s') % (advance.employee_id.name)
            move = {
                'narration': name,
                'date': advance.payment_date or time.strftime('%Y-%m-%d'),
                'journal_id': advance.journal_id.id,
            }

            amt = advance.paid_amount
            partner_id = default_partner_id
            debit_account_id = advance.debit_account_id.id
            credit_account_id = advance.credit_account_id.id

            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0

            # analytic_tags = self.env['account.analytic.tag']
            # analytic_tags += self.employee_id.analytic_tag_id
            # analytic_tags += self.employee_id.department_id.analytic_tag_id
            # analytic_tag_ids = [(6, 0, analytic_tags.ids)]

            if debit_account_id and not advance.payment_channel=='cash':
                debit_line = (0, 0, {
                    'name': name,
                    'date': advance.payment_date or time.strftime('%Y-%m-%d'),
                    'partner_id': partner_id,
                    'account_id': debit_account_id,
                    'journal_id': advance.journal_id.id,
                    'debit': amt > 0.0 and amt or 0.0,
                    'credit': amt < 0.0 and -amt or 0.0,
                    # 'analytic_tag_ids': analytic_tag_ids,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            # Credit Entry if payment mode is not Cash means it is Bank
            if credit_account_id and not advance.payment_channel=='cash':
                credit_line = (0, 0, {
                    'name': name,
                    'date': advance.payment_date or time.strftime('%Y-%m-%d'),
                    'partner_id': partner_id,
                    'account_id': credit_account_id,
                    'journal_id': advance.journal_id.id,
                    'debit': amt < 0.0 and -amt or 0.0,
                    'credit': amt > 0.0 and amt or 0.0,
                    # 'analytic_tag_ids': analytic_tag_ids,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            # Credit Entry If Payment mode is cash means to create entry directly in cashbook
            if credit_account_id and advance.payment_channel=='cash':
                statement_rec = self.env['account.bank.statement'].search([('date', '=', advance.date), ('state', '=', 'open'), ('journal_id', '=', 9)])
                if statement_rec:
                    line_vals = ({
                        'statement_id': statement_rec[0].id,
                        'name': name,
                        'journal_id': 9,
                        'company_id': self.env.company,
                        'date': advance.payment_date or time.strftime('%Y-%m-%d'),
                        'account_id': debit_account_id,
                        'entry_date': timenow,
                        'amount': -amt,
                    })
                    statement_line = self.env['account.bank.statement.line'].create(line_vals)

                    debit_line = (0, 0, {
                        'name': name,
                        'date': advance.payment_date or time.strftime('%Y-%m-%d'),
                        'partner_id': partner_id,
                        'account_id': debit_account_id,
                        'journal_id': advance.journal_id.id,
                        'debit': amt > 0.0 and amt or 0.0,
                        'credit': amt < 0.0 and -amt or 0.0,
                        # 'analytic_tag_ids': analytic_tag_ids,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                    # Credit Entry
                    credit_line = (0, 0, {
                        'name': name,
                        'date': advance.payment_date or time.strftime('%Y-%m-%d'),
                        'partner_id': partner_id,
                        'account_id': credit_account_id,
                        'journal_id': advance.journal_id.id,
                        'debit': amt < 0.0 and -amt or 0.0,
                        'credit': amt > 0.0 and amt or 0.0,
                        # 'analytic_tag_ids': analytic_tag_ids,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                else:
                    raise ValidationError(_('There is no CashBook entry Opened for this Date. May be Cashbook Validated.'))

            move.update({'line_ids': line_ids})
            move_id = move_pool.create(move)
            _logger.info('************* Move is Created %r ************', move_id.id)
            advance.move_id = move_id.id,
            _logger.info('********** Move Reference in Advance %r ***********', advance.move_id.id)
            advance.state = 'paid'
        # move_id.post()
        return True
