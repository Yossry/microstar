# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


class SaleCommission(models.Model):
    _name = "sale.commission"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sales Commission Types "

    name = fields.Char("Name", required=True, tracking=True)
    sequence = fields.Integer('Sequence', default=10)
    commission_type = fields.Selection(selection=[("fixed", "Fixed percentage"),
                                                  ("section", "By sections"),
                                                  ('fixed_amount', 'Fixed Amount')
                                                  ], string="Type", required=True, default="fixed", tracking=True)
    fix_qty = fields.Float(string="Fixed percentage", tracking=True)
    section_ids = fields.One2many(string="Sections", comodel_name="sale.commission.section", inverse_name="commission_id", )
    active = fields.Boolean(default=True, tracking=True)
    invoice_state = fields.Selection([("open", "Invoice Based"),
                                      ("paid", "Payment Based")
                                      ], string="Invoice Status", required=True, default="open")
    amount_base_type = fields.Selection(selection=[("gross_amount", "Gross Amount"),
                                                   ("net_amount", "Net Amount")
                                                   ], string="Base", required=True, default="gross_amount", tracking=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('lock', 'Locked')
                              ], string='Status', default='draft', tracking=True)

    _sql_constraints = [('name_unique', 'UNIQUE(name)', _('Name Duplicate!')), ]

    def action_lock(self):
        self.state = 'lock'

    def action_unlock(self):
        self.state = 'draft'

    def calculate_section(self, base):
        self.ensure_one()
        for section in self.section_ids:
            if section.amount_from <= base <= section.amount_to:
                return base * section.percent / 100.0
        return 0.0


class SaleCommissionSection(models.Model):
    _name = "sale.commission.section"
    _description = "Commission Section"

    commission_id = fields.Many2one("sale.commission", string="Commission")
    amount_from = fields.Float(string="From")
    amount_to = fields.Float(string="To")
    percent = fields.Float(string="Percent", required=True)

    @api.constrains("amount_from", "amount_to")
    def _check_amounts(self):
        for section in self:
            if section.amount_to < section.amount_from:
                raise exceptions.ValidationError(_("The lower limit cannot be greater than upper one."))
