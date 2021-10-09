{
    'name': 'Journal Entry Report',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'sequence': 5,
    'summary': 'Journal Entry Reports',
    'author': 'AARSOL',
    'website': 'https://aarsol.com/',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'base', 'mail', 'account'
    ],
    'data': [
        'reports/journal_entry_report.xml',
        'reports/journal_data.xml',
        'reports/report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
