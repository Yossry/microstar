{
    'name': 'HR Ext',
    'version': '14.0.1.2.0',
    'category': 'Human Resources/Employees',
    'sequence': 2,
    'summary': 'Additional Features in Human Resource',
    'author': 'AARSOL',
    'website': 'https://aarsol.com/',
    'license': 'AGPL-3',
    'images': [
        'static/src/img/default_image.png',
    ],
    'depends': [
        'hr', 'hr_payroll',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'menu/menu.xml',

        'views/hr_view.xml',
        'views/hr_employee_status_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_salary_inputs_view.xml',
        'views/hr_payslip_cron_view.xml',
        'views/hr_loan_rules_view.xml',
        'views/hr_employee_loan_view.xml',
        'views/hr_staff_advance_view.xml',
        'views/res_config_setting_view.xml',
        'views/hr_location_view.xml',

        'wizard/payslips_cron_wizard_view.xml',

        'reports/police_verification_report.xml',
        'reports/salary_report_view.xml',
        'reports/report_view.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
