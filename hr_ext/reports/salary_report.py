from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)
from io import StringIO, BytesIO
import io
import pdb

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


class SalaryReport(models.TransientModel):
    _name = 'employee.salary.report'
    _description = 'Employee Salary Report'

    department_ids = fields.Many2many('hr.department', 'hr_department_salary_rep_rel', 'rep_id', 'dept_id', string='Departments')
    date_from = fields.Date("From Date", default=lambda self: str(datetime.now() + relativedelta.relativedelta(day=1))[:10])
    date_to = fields.Date("To Date", default=lambda self: str(datetime.now() + relativedelta.relativedelta(day=31))[:10])

    def get_payslip_working_days(self, payslip_id=None, code=None):
        worked_day_obj = self.env['hr.payslip.worked_days']
        worked_day_id = worked_day_obj.search([('payslip_id', '=', payslip_id), ('code', '=', code)])
        return worked_day_id.number_of_days

    def get_payslip_lines(self, payslip_id, line_type=None, code=None):
        payslip_line_obj = self.env['hr.payslip.line']
        payslip_input_obj = self.env['hr.payslip.input']
        amount = 0
        if line_type=='payslip_line':
            payslip_line_id = payslip_line_obj.search([('slip_id', '=', payslip_id), ('code', '=', code)])
            amount = payslip_line_id.total or 0
        if line_type=='input_line':
            input_id = payslip_input_obj.search([('payslip_id', '=', payslip_id), ('code', '=', code)])
            amount = input_id.amount or 0
        return amount

    def get_deduction(self, payslip):
        deduction = 0
        deduction_lines = self.env['hr.payslip.line'].search([('category_id', '=', 4), ('slip_id', '=', payslip)])
        for line in deduction_lines:
            deduction = line.total + deduction

        return deduction

    def make_excel(self):
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet("Employee Salary Report")
        style_title = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center;borders: left thin, right thin, top thin, bottom thin;pattern: pattern solid,fore_colour aqua;")
        style_title1 = xlwt.easyxf(
            "font:height 200; font: name Liberation Sans, bold on,color black; align: horiz left;borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour silver_ega;")
        style_title2 = xlwt.easyxf(
            "font:height 210; font: name Liberation Sans, bold on,color black; align: horiz center;borders: left thin, right thin, top thin, bottom thin;pattern: pattern solid,fore_colour aqua;")
        style_table_header = xlwt.easyxf(
            "font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center;borders: left thin, right thin, top thin, bottom thin;pattern: pattern solid,fore_colour silver_ega;")
        style_ot_totals = xlwt.easyxf(
            "font:height 200; font: name Liberation Sans, bold on,color black; align: horiz left; pattern: pattern solid, fore_colour red;;borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour rose;")
        style_date_col2 = xlwt.easyxf(
            "font:height 180; font: name Liberation Sans,color black; align: horiz left;borders: left thin, right thin, top thin, bottom thin;")
        style_date_col = xlwt.easyxf(
            "font:height 180; font: name Liberation Sans,color black; align: horiz right;borders: left thin, right thin, top thin, bottom thin;")

        ttime = fields.Datetime.now() + timedelta(hours=+5)
        worksheet.write_merge(0, 2, 0, 27, self.env.company.name, style=style_title)
        worksheet.write_merge(3, 4, 0, 27, 'Employee Monthly Attendance Days Report From ' + self.date_from.strftime('%d-%m-%Y') + " To " + self.date_to.strftime('%d-%m-%Y'), style=style_table_header)

        # col width
        col0 = worksheet.col(0)
        col0.width = 256 * 8
        col1 = worksheet.col(1)
        col1.width = 256 * 20
        col2 = worksheet.col(2)
        col2.width = 256 * 35
        col3 = worksheet.col(3)
        col3.width = 256 * 25
        col4 = worksheet.col(4)
        col4.width = 256 * 25
        col5 = worksheet.col(5)
        col5.width = 256 * 20
        col6 = worksheet.col(6)
        col6.width = 256 * 20
        col7 = worksheet.col(7)
        col7.width = 256 * 20
        col8 = worksheet.col(8)
        col8.width = 256 * 25
        col9 = worksheet.col(9)
        col9.width = 256 * 20
        col10 = worksheet.col(10)
        col10.width = 256 * 20
        col11 = worksheet.col(11)
        col11.width = 256 * 20
        col12 = worksheet.col(12)
        col12.width = 256 * 20
        col13 = worksheet.col(13)
        col13.width = 256 * 25
        col14 = worksheet.col(14)
        col14.width = 256 * 25
        col15 = worksheet.col(15)
        col15.width = 256 * 20
        col16 = worksheet.col(16)
        col16.width = 256 * 20
        col17 = worksheet.col(17)
        col17.width = 256 * 20
        col18 = worksheet.col(18)
        col18.width = 256 * 20
        col19 = worksheet.col(19)
        col19.width = 256 * 20
        col20 = worksheet.col(20)
        col20.width = 256 * 20

        col21 = worksheet.col(21)
        col21.width = 256 * 20
        col22 = worksheet.col(22)
        col22.width = 256 * 20
        col23 = worksheet.col(23)
        col23.width = 256 * 20
        col24 = worksheet.col(24)
        col24.width = 256 * 20
        col25 = worksheet.col(25)
        col25.width = 256 * 20
        col26 = worksheet.col(26)
        col26.width = 256 * 20
        col27 = worksheet.col(27)
        col27.width = 256 * 35
        col28 = worksheet.col(28)
        col28.width = 256 * 20

        row = 5
        col = 0
        table_header = ['SR#', 'Code', 'Name', 'Father Name', 'CNIC', 'Joining Date', 'Designation',
                        'Basic Salary', 'Working Days', 'Leaves', 'Absent', 'Days Worked', 'Total Salary', 'Travelling Allowance', 'Mobile Allowance ', 'Laundry Allowance',
                        'Medical Reimbursement', 'Incentive', 'Arrears', 'Over Time', 'Total Allowances, overtime, arrears and reimbursements', 'Loans', 'Advances', 'Taxation',
                        'EOBI', 'Total Deductions', 'Net Salary Payable', 'Remarks']

        for i in range(28):
            worksheet.write(row, col, table_header[i], style=style_table_header)
            col += 1

        row += 1
        col = 0
        worksheet.write_merge(row, row, 0, 6, "Personal Information", style=style_title2)
        worksheet.write_merge(row, row, 7, 12, "", style=style_title2)
        worksheet.write_merge(row, row, 13, 22, "Allowances", style=style_title2)
        worksheet.write_merge(row, row, 23, 27, "Deductions", style=style_title2)
        # worksheet.write_merge(row, row, 28, 28, "", style=style_title2)

        employees = False
        if self.department_ids:
            employees = self.env['hr.employee'].search([('department_id', 'in', self.department_ids.ids)])
        else:
            employees = self.env['hr.employee'].search([])

        if employees:
            total_basic = 0
            total_transport = 0
            total_mobile = 0
            total_laundry = 0
            total_medical = 0
            total_arrears = 0
            total_incentives = 0
            total_ot = 0

            total_allowances = 0
            total_gross = 0

            total_tax = 0
            total_loan = 0
            total_advance = 0
            total_eobi = 0
            total_deductions = 0
            total_net = 0

            payslips = self.env['hr.payslip'].search([('employee_id', 'in', employees.ids), ('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])

            if payslips:
                sr = 1
                for payslip in payslips:
                    remarks = ''
                    total_basic = total_basic + self.get_payslip_lines(payslip.id, 'payslip_line', 'BASIC')
                    total_transport = total_transport + self.get_payslip_lines(payslip.id, 'payslip_line', 'TRA')
                    total_mobile = total_mobile + self.get_payslip_lines(payslip.id, 'payslip_line', 'MBA')
                    total_laundry = total_laundry + self.get_payslip_lines(payslip.id, 'payslip_line', 'LDRYA')
                    total_medical = total_medical + self.get_payslip_lines(payslip.id, 'payslip_line', 'MEDRE')
                    total_incentives = total_incentives + self.get_payslip_lines(payslip.id, 'payslip_line', 'INCT')
                    total_arrears = total_arrears + self.get_payslip_lines(payslip.id, 'payslip_line', 'ARS')
                    total_ot = total_ot + self.get_payslip_lines(payslip.id, 'payslip_line', 'OT')
                    total_allowances = total_allowances + 0
                    total_gross = total_gross + self.get_payslip_lines(payslip.id, 'payslip_line', 'GROSS')

                    total_loan = total_loan + self.get_payslip_lines(payslip.id, 'payslip_line', 'LOAN')
                    total_advance = total_advance + self.get_payslip_lines(payslip.id, 'payslip_line', 'ADV')
                    total_tax = total_tax + self.get_payslip_lines(payslip.id, 'payslip_line', 'TAX')
                    total_eobi = total_eobi + self.get_payslip_lines(payslip.id, 'payslip_line', 'EOBI')
                    total_deductions = total_deductions + 0
                    total_net = total_net + self.get_payslip_lines(payslip.id, 'payslip_line', 'NET')

                    row += 1
                    col = 0
                    worksheet.write(row, col, sr, style=style_date_col2)
                    col += 1
                    worksheet.write(row, col, payslip.employee_id.code and payslip.employee_id.code or '', style=style_date_col2)
                    col += 1
                    worksheet.write(row, col, payslip.employee_id.name and payslip.employee_id.name or '', style=style_date_col2)
                    col += 1
                    worksheet.write(row, col, payslip.employee_id.father_name and payslip.employee_id.father_name or '', style=style_date_col2)
                    col += 1
                    worksheet.write(row, col, payslip.employee_id.cnic and payslip.employee_id.cnic or '', style=style_date_col2)
                    col += 1
                    worksheet.write(row, col, payslip.employee_id.joining_date and str(payslip.employee_id.joining_date) or '', style=style_date_col2)
                    col += 1
                    worksheet.write(row, col, payslip.employee_id.job_id and payslip.employee_id.job_id.name or '', style=style_date_col2)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'BASIC'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_working_days(payslip.id, 'MAX'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, 0, style=style_date_col)
                    col += 1
                    worksheet.write(row, col, 0, style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_working_days(payslip.id, 'WORK100'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'GROSS'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'TRA'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'MBA'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'LDRYA'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', '	MEDRE'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'INCT'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'ARS'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'OT'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, '', style=style_date_col)
                    col += 1

                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'LOAN'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'ADV'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'TAX'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'EOBI'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, '', style=style_date_col)
                    col += 1
                    worksheet.write(row, col, self.get_payslip_lines(payslip.id, 'payslip_line', 'NET'), style=style_date_col)
                    col += 1
                    worksheet.write(row, col, remarks, style=style_date_col)
                    col += 1
                    sr += 1

                row += 1
                worksheet.write_merge(row, row, 0, 6, "", style=style_title2)
                worksheet.write_merge(row, row, 7, 7, total_basic, style=style_title2)
                worksheet.write_merge(row, row, 8, 8, '', style=style_title2)
                worksheet.write_merge(row, row, 9, 9, '', style=style_title2)
                worksheet.write_merge(row, row, 10, 10, '', style=style_title2)
                worksheet.write_merge(row, row, 11, 11, '', style=style_title2)
                worksheet.write_merge(row, row, 12, 12, total_gross, style=style_title2)
                worksheet.write_merge(row, row, 13, 13, total_transport, style=style_title2)
                worksheet.write_merge(row, row, 14, 14, total_mobile, style=style_title2)
                worksheet.write_merge(row, row, 15, 15, total_laundry, style=style_title2)
                worksheet.write_merge(row, row, 16, 16, total_medical, style=style_title2)
                worksheet.write_merge(row, row, 17, 17, total_incentives, style=style_title2)
                worksheet.write_merge(row, row, 18, 18, total_arrears, style=style_title2)
                worksheet.write_merge(row, row, 19, 19, total_ot, style=style_title2)
                worksheet.write_merge(row, row, 20, 20, total_allowances, style=style_title2)

                worksheet.write_merge(row, row, 21, 21, total_loan, style=style_title2)
                worksheet.write_merge(row, row, 22, 22, total_advance, style=style_title2)
                worksheet.write_merge(row, row, 23, 23, total_tax, style=style_title2)
                worksheet.write_merge(row, row, 24, 24, total_eobi, style=style_title2)
                worksheet.write_merge(row, row, 25, 25, total_deductions, style=style_title2)
                worksheet.write_merge(row, row, 26, 26, total_net, style=style_title2)
                worksheet.write_merge(row, row, 27, 27, "", style=style_title2)

        file_data = io.BytesIO()
        workbook.save(file_data)

        wiz_id = self.env['payroll.reports.save.wizard'].create({
            'data': base64.encodebytes(file_data.getvalue()),
            'name': 'Employee Salary Report.xls'
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Salary Report',
            'res_model': 'payroll.reports.save.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [[False, 'form']],
            'res_id': wiz_id.id,
            'target': 'new',
            'context': self._context,
        }
