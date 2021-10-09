# -*- coding: utf-8 -*-
import pdb
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayments(models.Model):
    _inherit = 'account.payment'

    apply_manual_currency_exchange = fields.Boolean(string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(string='Manual Currency Exchange Rate')
    active_manual_currency_rate = fields.Boolean('active Manual Currency', default=False)
    check_payment_from_dashboard = fields.Boolean(default=False)

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        if self.currency_id:
            if self.company_id.currency_id!=self.currency_id:
                self.active_manual_currency_rate = True
            else:
                self.active_manual_currency_rate = False
        else:
            self.active_manual_currency_rate = False

    @api.model
    def default_get(self, fields):
        result = super(AccountPayments, self).default_get(fields)
        if self.check_payment_from_dashboard!=False:
            move_id = self.env['account.move'].browse(self._context.get('active_ids')).filtered(
                lambda move: move.is_invoice(include_receipts=True))

            result.update({
                'apply_manual_currency_exchange': move_id.apply_manual_currency_exchange,
                'manual_currency_exchange_rate': move_id.manual_currency_exchange_rate
            })
        return result

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        pdb.set_trace()
        write_off_line_vals = write_off_line_vals or {}
        if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
            raise UserError(_("You can't create a new payment without an outstanding payments/receipts account set on the %s journal.", self.journal_id.display_name))

        # Compute amounts.
        write_off_amount = write_off_line_vals.get('amount', 0.0)
        if self.payment_type=='inbound':
            # Receive money.
            counterpart_amount = -self.amount
            write_off_amount *= -1
        elif self.payment_type=='outbound':
            # Send money.
            counterpart_amount = self.amount
        else:
            counterpart_amount = 0.0
            write_off_amount = 0.0

        # Added from line 286 to 309
        # Manage currency.
        company_currency = self.company_id.currency_id
        counterpart_amount_currency = counterpart_amount
        write_off_amount_currency = write_off_amount
        currency_id = self.currency_id.id

        if self.currency_id==company_currency:
            # Single-currency.
            balance = counterpart_amount
            counterpart_amount_currency = counterpart_amount
            write_off_balance = write_off_amount
            counterpart_amount = write_off_amount = 0.0
            currency_id = False
        else:
            if self.active_manual_currency_rate:
                if self.apply_manual_currency_exchange:
                    # balance = counterpart_amount / payment.manual_currency_exchange_rate
                    balance = counterpart_amount * self.manual_currency_exchange_rate
                    write_off_balance = write_off_amount * self.manual_currency_exchange_rate
                else:
                    balance = self.currency_id._convert(counterpart_amount, self.company_id.currency_id, self.company_id, self.date)
                    write_off_balance = self.currency_id._convert(write_off_amount, self.company_id.currency_id, self.company_id, self.date)
            else:
                balance = self.currency_id._convert(counterpart_amount, self.company_id.currency_id, self.company_id, self.date)
                write_off_balance = self.currency_id._convert(write_off_amount, self.company_id.currency_id, self.company_id, self.date)

        if self.is_internal_transfer:
            if self.payment_type=='inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else:  # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.
        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }

        default_line_name = self.env['account.move.line']._get_default_line_name(
            payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': -counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': balance < 0.0 and -balance or 0.0,
                'credit': balance > 0.0 and balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.journal_id.payment_debit_account_id.id if balance < 0.0 else self.journal_id.payment_credit_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency + write_off_amount_currency if currency_id else 0.0,
                'currency_id': currency_id,
                'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        if write_off_balance:
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency': -write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })
        return line_vals_list

