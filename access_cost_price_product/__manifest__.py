# -*- coding: utf-8 -*-
{
    "name": "Hide cost price, product",
    "summary": "Hide cost price, hide standard price, hide product price, hide product cost price",
    "description": "The cost price can only be accessed through Access Group.",
    "version": "14.0.1",
    "category": "Access Right",
    
    # "price": 2.99,
    # "currency": "USD",
    "support": "info@acruxlab.com",
    "website": "https://acruxlab.com",
    "license": "OPL-1",
    "author": "AcruxLab",
    "images": ['static/description/Banner.png'],

    "depends": ['product','stock'],
    "data": [
        'security/security.xml',
        'views/product_template.xml',
        'views/product_product.xml'
    ],
    "application": False,
    "installable": True,
}
