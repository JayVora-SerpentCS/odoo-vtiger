# -*- coding: utf-8 -*-
{
    'name': 'Product VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Product VTiger Integration',
    'description': """
        Product VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt Ltd',
    'website': 'https://www.serpentcs.com',
    'category': 'Product',
    'depends': [
        'vtiger_connector_partner',
        'stock',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
}
