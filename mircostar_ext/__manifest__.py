{
    'name': 'NOHA General Configuration',
    'version': '13.0.1.2.0',
    'category': 'Sales/Sales',
    'sequence': 3,
    'summary': 'Additional In Product Management',
    'author': 'AARSOL',
    'website': 'https://aarsol.com/',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'base', 'mail', 'product'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
