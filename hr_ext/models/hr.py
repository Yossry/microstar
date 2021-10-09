import re
import time
from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DFORMAT


def parse_date(td):
    resYear = float(td.days) / 365.0
    resMonth = (resYear - int(resYear)) * 365.0 / 30.0
    resDays = int((resMonth - int(resMonth)) * 30)
    resYear = int(resYear)
    resMonth = int(resMonth)
    return (resYear and (str(resYear) + "Y ") or "") + (resMonth and (str(resMonth) + "M ") or "") + (
            resMonth and (str(resDays) + "D") or "")


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    father_name = fields.Char('Father / Husband Name', tracking=True)
    employee_address = fields.Char('Address')

    code = fields.Char('Code', tracking=True)
    cnic = fields.Char('CNIC', size=15, tracking=True)
    age = fields.Char("Age", compute='_compute_age')

    joining_date = fields.Date('Joining Date', tracking=True)
    bank_account_title = fields.Char('Account Title', tracking=True)
    bank_account_no = fields.Char('Account No', tracking=True)
    bank_id = fields.Many2one('res.bank', 'Bank', tracking=True)

    status = fields.Many2one('hr.employee.status', 'Employee Status', tracking=True, index=True)
    profile_status = fields.Selection([('draft', 'Draft'),
                                       ('lock', 'Lock'),
                                       ], default='draft', string='Profile Status')

    biometric_code = fields.Char('Biometric Code')
    location_id = fields.Many2one('hr.location', 'Location', index=True, tracking=True)

    def name_get(self):
        res = []
        for record in self:
            name = (record.code or '') + ' - ' + record.name
            res.append((record.id, name))
        return res

    def _compute_age(self):
        for rec in self:
            if rec.birthday:
                start = datetime.strptime(str(rec.birthday), OE_DFORMAT)
                end = datetime.strptime(str(time.strftime(OE_DFORMAT)), OE_DFORMAT)
                delta = end - start
                rec.age = parse_date(delta)
            else:
                rec.age = ''

    @api.constrains('cnic')
    def _check_cnic(self):
        for rec in self:
            if rec.cnic:
                cnic_com = re.compile('^[0-9+]{5}-[0-9+]{7}-[0-9]{1}$')
                a = cnic_com.search(rec.cnic)
                if a:
                    return True
                else:
                    raise UserError(_("CNIC Format is Incorrect. Format Should like this 00000-0000000-0"))

    def action_lock(self):
        for rec in self:
            rec.profile_status = 'lock'

    def action_unlock(self):
        for rec in self:
            rec.profile_status = 'draft'


class HREmployeeStatus(models.Model):
    _name = 'hr.employee.status'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Status"

    name = fields.Char('Name', tracking=True)
    code = fields.Char('Code', tracking=True)
    active = fields.Boolean('Active', default=True)
