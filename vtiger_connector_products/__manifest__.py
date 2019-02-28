# -*- coding: utf-8 -*-
{
    'name': 'Products VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Products VTiger Integration',
    'description': """
        Products VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': 'Sales',
    'depends': ['product',
                'vtiger_connector_base'],
    'data': [
        'views/res_company_view.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
}
