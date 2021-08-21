from datetime import date
from odoo.exceptions import UserError
from odoo import models, fields, api, _


class HRHolidaysPublic(models.Model):
    _name = 'hr.holidays.public'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Public Holidays'
    _rec_name = 'year'
    _order = "year"

    year = fields.Char("Calendar Year", required=True)
    line_ids = fields.One2many('hr.holidays.public.line', 'holidays_id', 'Holiday Dates')
    country_id = fields.Many2one('res.country', 'Country')

    @api.constrains('year', 'country_id')
    def _check_year(self):
        for data in self:
            if not data.country_id:
                ids = self.search([('year', '=', data.year), ('country_id', '=', False), ('id', '!=', data.id)])
                if ids:
                    raise UserError(_("Error: Duplicate year"))
        return True

    _sql_constraints = [('year_unique', 'UNIQUE(year,country_id)', _('Duplicate year and country!')), ]

    def is_public_holiday(self, dt, employee_id=None):
        employee = self.env['hr.employee'].browse(employee_id)
        holidays_filter = [('year', '=', dt.year)]
        if not employee or not employee.address_id.country_id:
            holidays_filter.append(('country_id', '=', False))
        else:
            holidays_filter += ['|', ('country_id', '=', employee.address_id.country_id.id), ('country_id', '=', False)]
        ph_ids = self.search(holidays_filter)
        if not ph_ids:
            return False

        states_filter = [('holidays_id', 'in', ph_ids)]
        if not employee or not employee.address_id.state_id:
            states_filter.append(('state_ids', '=', False))
        else:
            states_filter += ['|', ('state_ids', '=', False), ('state_ids.id', '=', employee.address_id.state_id.id)]

        hr_holiday_public_line_obj = self.env['hr.holidays.public.line']
        holidays_line_ids = hr_holiday_public_line_obj.search(states_filter)
        for line in holidays_line_ids:
            if date.strftime(dt, "%Y-%m-%d")==line.date:
                return True
        return False

    def get_holidays_list(self, year, employee_id=None):
        res = []
        employee = self.env['hr.employee'].browse(employee_id)
        holidays_filter = [('year', '=', year)]
        if not employee or not employee.address_id.country_id:
            holidays_filter.append(('country_id', '=', False))
        else:
            holidays_filter += ['|', ('country_id', '=', employee.address_id.country_id.id), ('country_id', '=', False)]
        ph_ids = self.search(holidays_filter)
        if not ph_ids:
            return res
        states_filter = [('holidays_id', 'in', ph_ids)]
        if not employee or not employee.address_id.state_id:
            states_filter.append(('state_ids', '=', False))
        else:
            states_filter += ['|', ('state_ids', '=', False), ('state_ids.id', '=', employee.address_id.state_id.id)]
        hr_holiday_public_line_obj = self.env['hr.holidays.public.line']
        holidays_line_ids = hr_holiday_public_line_obj.search(states_filter)
        [res.append(l.date) for l in holidays_line_ids]
        return res


class HRHolidaysLine(models.Model):
    _name = 'hr.holidays.public.line'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Public Holidays Lines'
    _order = "date, name desc"

    name = fields.Char('Name', size=128, required=True, translate=True)
    date = fields.Date('Date', required=True)
    holidays_id = fields.Many2one('hr.holidays.public', 'Holiday Calendar Year')
    variable = fields.Boolean('Date may change')
    state_ids = fields.Many2many('res.country.state', 'hr_holiday_public_state_rel', 'line_id', 'state_id', 'Related states')
