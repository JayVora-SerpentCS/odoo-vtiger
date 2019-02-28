# -*- coding: utf-8 -*-
{
    'name': 'Purchase VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Purchase VTiger Integration',
    'description': """
        Purchase VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': 'Purchases',
    'depends': [
        'vtiger_connector_products',
        'vtiger_connector_partner',
        'purchase',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/purchase_view.xml',
    ],
    'installable': True,
}
