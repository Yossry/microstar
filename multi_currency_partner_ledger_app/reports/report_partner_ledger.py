# -*- coding: utf-8 -*-
import pdb

from odoo import api, models, fields


class MultiReportPartnerLedger(models.AbstractModel):
    _name = 'report.multi_currency_partner_ledger_app.report_partnerledger'

    def _lines(self, data, partner, currency):
        domain = [('move_id.partner_id','=', partner.id), ('move_id.currency_id','=', currency.id)]            
        move_state = data['move_state']
        if move_state == ['posted']:
            domain +=[('move_id.state','=', 'posted')]
        else:
            domain +=[('move_id.state','in', ['draft','posted'])]
        
        account_type = data['account_type']
        if account_type == ['supplier']:
            domain +=[('account_id.internal_type', '=', 'payable')]
        elif account_type == ['customer']:
            domain +=[('account_id.internal_type', '=', 'receivable')]
        else:
            domain +=[('account_id.internal_type', 'in', ['receivable', 'payable'])]
        
        if data['date_from'] and not data['date_to']:
            domain +=[('date', '>=', data['date_from'])]
        elif data['date_to'] and not data['date_from']:
            domain +=[('date', '<=', data['date_to'])]
        elif data['date_from'] and data['date_to']:
            domain +=[('date', '>=', data['date_from']),('date', '<=', data['date_to'])]
        else:
            domain +=[]
        invoice_ids = self.env['account.move.line'].search(domain)
        full_account = []
        for invoice in invoice_ids:
            displayed_name = str(invoice.move_id.name or '') + '-' + str(invoice.move_id.payment_reference or '')
            # pdb.set_trace()
            vals = {
                'debit' : invoice.debit,
                'credit' : invoice.credit,
                'amount_currency' : invoice.amount_currency,
                'progress': invoice.balance,
                'date': invoice.move_id.invoice_date,
                'date_due': invoice.move_id.invoice_date_due,
                'code' : invoice.journal_id.code,
                'lines_id': invoice.move_id.invoice_line_ids,
                'a_code' : invoice.account_id.code,

                'displayed_name': displayed_name,
                'currency_id': invoice.currency_id.symbol,
                'invoice_id': invoice.move_id.id
            }
            full_account.append(vals)
        return full_account

    def _sum_partner(self, data, partner, currencys):
        total_credit = 0.0
        total_debit = 0.0
        total_balance = 0.0
        total_amount_lst = []
        for currency in currencys:
            records = self._lines(data, partner, currency)
            for record in records:
                total_credit += record['credit']
                total_debit  += record['debit']
                total_balance  += record['progress']
        total_amount_lst.append({'total_credit': total_credit,
                                 'total_debit': total_debit,
                                 'total_balance': total_balance})
        return total_amount_lst

    @api.model
    def _get_report_values(self, docids, data=None):
        context = data.get('context')
        currency_ids = self.env['res.currency'].browse(context.get('currency_ids'))
        partner_ids = self.env['res.partner'].browse(data.get('docs'))
        return {
            'currency_ids': currency_ids,
            'doc_model': self.env['res.partner'],
            'docs': partner_ids,
            'lines': self._lines,
            'extra': data,
            'sum_partner': self._sum_partner,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: