# -*- coding: utf-8 -*-
{
    'name': 'CRM VTiger Integration',
    'version': '11.0.1.0.0',
    'summary': 'CRM VTiger Integration',
    'description': """
        CRM VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': '',
    'depends': [
        'vtiger_connector_partner',
        'crm',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/crm_view.xml',
    ],
    'installable': True,
}
