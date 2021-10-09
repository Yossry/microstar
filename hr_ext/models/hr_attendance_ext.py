from datetime import date, datetime, time
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import pdb
import logging

_logger = logging.getLogger(__name__)


class HRAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        pass

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee."""
        pass
