# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    apply_manual_currency_exchange = fields.Boolean(string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(string='Manual Currency Exchange Rate')
    active_manual_currency_rate = fields.Boolean('active Manual Currency', default=False)
    check_payment_from_dashboard = fields.Boolean(default=False)

    def _create_payment_vals_from_wizard(self):
        payment_values = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        payment_values['apply_manual_currency_exchange'] = self.apply_manual_currency_exchange
        payment_values['manual_currency_exchange_rate'] = self.manual_currency_exchange_rate
        payment_values['active_manual_currency_rate'] = self.active_manual_currency_rate
        payment_values['check_payment_from_dashboard'] = self.check_payment_from_dashboard
        return payment_values

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'manual_currency_exchange_rate')
    def _compute_amount(self):
        for wizard in self:
            if wizard.source_currency_id==wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency
            elif wizard.currency_id==wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                if wizard.active_manual_currency_rate:
                    if wizard.apply_manual_currency_exchange:
                        amount_payment_currency = wizard.source_amount / wizard.manual_currency_exchange_rate
                        wizard.amount = amount_payment_currency
                else:
                    amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
                    wizard.amount = amount_payment_currency

    @api.depends('amount')
    def _compute_payment_difference(self):
        for wizard in self:
            if wizard.source_currency_id==wizard.currency_id:
                # Same currency.
                wizard.payment_difference = wizard.source_amount_currency - wizard.amount
            elif wizard.currency_id==wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.payment_difference = wizard.source_amount - wizard.amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                if wizard.active_manual_currency_rate:
                    if wizard.apply_manual_currency_exchange:
                        amount_payment_currency = wizard.source_amount / wizard.manual_currency_exchange_rate
                        wizard.payment_difference = amount_payment_currency - wizard.amount
                else:
                    amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
                    wizard.payment_difference = amount_payment_currency - wizard.amount
