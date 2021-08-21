from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    loan_input_rule = fields.Many2one("hr.salary.inputs", config_parameter='hr_ext.loan_input_rule', string="Loan Input Type")
    advance_input_rule = fields.Many2one("hr.salary.inputs", config_parameter='hr_ext.advance_input_rule', string="Advance Input Type")

    attendance_policy = fields.Selection([('none', 'No Attendance'),
                                          ('daily', 'Daily Attendance'),
                                          ('monthly', 'Monthly Attendance'),
                                          ('overtime', 'Overtime'),
                                          ('bio_month', 'Bio Device with Monthly Counting')
                                          ], config_parameter='hr_ext.attendance_policy', default='monthly', string='Attendance Policy')
