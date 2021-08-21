# -*- coding: utf-8 -*-
import time
import tempfile
import binascii
import xlrd
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
from io import StringIO
import io
from odoo.exceptions import UserError, ValidationError
import pdb

import logging

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class MonthlyOvertimeImportWizard(models.TransientModel):
    _name = "monthly.overtime.import.wizard"
    _description = 'Overtime import Through Excel File'

    file = fields.Binary('File')
    sequence_opt = fields.Selection([('custom', 'Use Excel/CSV Sequence Number'),
                                     ('system', 'Use System Default Sequence Number')
                                     ], string='Sequence Option', default='custom')
    import_option = fields.Selection([('csv', 'CSV File'),
                                      ('xls', 'XLS File')
                                      ], string='Select', default='xls')

    def action_import_overtime(self):
        """Load data from the CSV file."""
        if self.import_option=='csv':
            keys = ['barcode']
            data = base64.b64decode(self.file)
            file_input = io.StringIO(data.decode("utf-8"))
            file_input.seek(0)
            reader_info = []
            reader = csv.reader(file_input, delimiter=',')

            try:
                reader_info.extend(reader)
            except Exception:
                raise exceptions.Warning(_("Not a valid file!"))
            values = {}
            for i in range(len(reader_info)):
                # val = {}
                field = list(map(str, reader_info[i]))
                values = dict(zip(keys, field))
                if values:
                    if i==0:
                        continue
                    else:
                        values.update({'option': self.import_option, 'seq_opt': self.sequence_opt})
                        res = self.make_sale(values)
        else:
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)

            overtime_list = []
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = list(map(lambda row: row.value.encode('utf-8'), sheet.row(row_no)))
                else:
                    line = list(map(lambda row: str(row.value), sheet.row(row_no)))
                    employee_code = line[0]
                    vals = employee_code.split('.')
                    if vals:
                        employee_code = vals[0]
                    if employee_code:
                        employee_id = self.env['hr.employee'].search([('code', '=', employee_code)])
                        if employee_id:
                            # if row[13].ctype == 3:  # Date
                            order_date = False
                            if line[1]:
                                date_value = xlrd.xldate_as_tuple(float(line[1]), workbook.datemode)
                                ot_date = date(*date_value[:3]).strftime('%Y-%m-%d')

                            data_values = {
                                'employee_id': employee_id.id,
                                'employee_code': employee_id.code and employee_id.code or '',
                                'department_id': employee_id.department_id and employee_id.department_id.id or False,
                                'date': ot_date and ot_date or False,
                                'duration': line[2] and float(line[2]) or 0,
                                'minutes': line[3] and float(line[3]) or 0,
                            }
                            ot_new_rec = self.env['hr.employee.monthly.overtime'].create(data_values)
                            overtime_list.append(ot_new_rec.id)
            if overtime_list:
                overtime_list = overtime_list
                form_view = self.env.ref('aarsol_hr_attendance_ext.view_hr_employee_monthly_overtime_form')
                tree_view = self.env.ref('aarsol_hr_attendance_ext.view_hr_employee_monthly_overtime_tree')
                return {
                    'domain': [('id', 'in', overtime_list)],
                    'name': _('Monthly Overtimes'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'hr.employee.monthly.overtime',
                    'view_id': False,
                    'views': [
                        (tree_view and tree_view.id or False, 'tree'),
                        (form_view and form_view.id or False, 'form'),
                    ],
                    'type': 'ir.actions.act_window'
                }
            else:
                return {'type': 'ir.actions.act_window_close'}
