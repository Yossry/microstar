from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError, AccessError
import pdb


class AccountAccount(models.Model):
    _inherit = 'account.account'
    _order = "code"


class AccountMove(models.Model):
    _inherit = 'account.move'

    voucher_type = fields.Selection([('BPV', 'BPV'),
                                     ('CPV', 'CPV'),
                                     ('BRV', 'BRV'),
                                     ('CRV', 'CRV'),
                                     ('JV', 'JV'),
                                     ('PV', 'PV'),
                                     ], string='Voucher Type')

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.invoice_filter_type_domain or 'general'
            domain = [('company_id', '=', m.company_id.id), ('type', '=', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

    @api.depends('company_id', 'invoice_filter_type_domain', 'voucher_type')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.invoice_filter_type_domain or 'general'
            if journal_type=='general' and m.voucher_type:
                if m.voucher_type in ('BPV', 'BRV'):
                    domain = [('company_id', '=', m.company_id.id), ('type', 'in', ('bank', 'general'))]
                    m.journal_id = self.env['account.journal'].search(domain, order='id desc', limit=1)
                    if not m.journal_id:
                        m.journal_id = self.env['account.journal'].search([('company_id', '=', m.company_id.id), ('type', '=', 'general')], order='id desc', limit=1)
                elif m.voucher_type in ('CPV', 'CRV'):
                    domain = [('company_id', '=', m.company_id.id), ('type', 'in', ('cash', 'general'))]
                    m.journal_id = self.env['account.journal'].search(domain, order='id desc', limit=1)
                    if not m.journal_id:
                        m.journal_id = self.env['account.journal'].search([('company_id', '=', m.company_id.id), ('type', '=', 'general')], order='id desc', limit=1)
                elif m.voucher_type in ('JV', 'PV'):
                    domain = [('company_id', '=', m.company_id.id), ('type', '=', 'general')]
                    m.journal_id = self.env['account.journal'].search(domain, order='id desc', limit=1)
                else:
                    domain = [('company_id', '=', m.company_id.id), ('type', '=', journal_type)]
                    m.journal_id = self.env['account.journal'].search(domain, order='id desc', limit=1)
            else:
                domain = [('company_id', '=', m.company_id.id), ('type', '=', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)
