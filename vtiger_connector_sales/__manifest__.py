# -*- coding: utf-8 -*-
{
    'name': 'Sale VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Sale VTiger Integration',
    'description': """
        Sale VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': '',
    'depends': [
        'vtiger_connector_products',
        'vtiger_connector_partner',
        'vtiger_connector_crm',
        'sale',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
}
