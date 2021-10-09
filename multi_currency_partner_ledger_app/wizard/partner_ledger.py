# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Accounting_reportPartner_ledger(models.TransientModel):
    _name = "multicurrency.partnerledger"

    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    currency_ids = fields.Many2many('res.currency', string='Currency', required=True,
                                   default=lambda self: self.env['res.currency'].search([]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    reconciled = fields.Boolean('Show Initial Balance')
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's Account", required=True, default='customer')
    partner_ids = fields.Many2many('res.partner','rel_multicurrency_partner',
                                   'multicurrency_id','partner_id',
                                   string="Partner's")

    def print_partner_ledger(self):
        data = {}
        used_context = {'currency_ids': [a.id for a in self.currency_ids]}
        data['move_state'] = ['draft', 'posted']
        if self.target_move == 'posted':
            data['move_state'] = ['posted']
        result_selection = self.result_selection
        if result_selection == 'supplier':
            data['account_type'] = ['supplier']
        elif result_selection == 'customer':
            data['account_type'] = ['customer']
        else:
            data['account_type'] = ['customer', 'supplier']

        data['date_from'] = self.date_from
        data['date_to'] = self.date_to

        final_dict = {
            'data': data,
            'docs': self.partner_ids.ids,
            'target_move': self.target_move,
            'account_type': self.result_selection,
            'reconciled': self.reconciled,
            'date_from' : self.date_from,
            'date_to' : self.date_to,
        }
        return self.env.ref('multi_currency_partner_ledger_app.multi_currency_partner_ledger').with_context(
                used_context).report_action(self, data=final_dict)
     

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
