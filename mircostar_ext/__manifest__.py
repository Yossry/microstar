{
    'name': 'MICRO Star',
    'version': '14.0.1.2.0',
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

        'views/product_brand_view.xml',
        'views/product_ext_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
