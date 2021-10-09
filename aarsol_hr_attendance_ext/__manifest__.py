{
    'name': 'HR Attendance Extensions',
    'version': '1.0',
    'category': 'Generic Modules/Human Resources',
    'description': """Employee Shift Scheduling""",
    'author': "AARSOL",
    'website': 'http://www.aarsol.com',
    'license': 'AGPL-3',
    'depends': [
        'hr_attendance',
    ],
    "external_dependencies": {
        'python': ['dateutil'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/data.xml',
        'menu/menu.xml',

        'views/hr_month_attendance_view.xml',
        'views/hr_overtime_view.xml',
        'views/hr_public_holidays_view.xml',
        'views/attendance_variation_view.xml',
        'views/hr_monthly_overtime_view.xml',
        'views/res_config_settings_views.xml',

        'wizard/confirm_overtime_view.xml',
        'wizard/approve_overtime_view.xml',
        'wizard/verify_overtime_view.xml',
        'wizard/validate_holidays_view.xml',
        'wizard/monthly_attendance_wizard_view.xml',
        'wizard/monthly_overtime_import_wizard_view.xml',

        'wizard/overtime_inputs_wizard_view.xml',
        'wizard/daily_attendance_wizard_view.xml',
        'wizard/attendance_wizard_view.xml',
        'wizard/leaves_report_wizard_view.xml',

        'report/report.xml',
        'report/report_dailyattendance.xml',
        'report/report_attendance.xml',
        # 'report/report_annual_attendance.xml',


    ],
    'test': [
    ],
    'installable': True,
    'application': True,
}
