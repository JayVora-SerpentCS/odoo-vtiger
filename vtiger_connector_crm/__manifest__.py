# -*- coding: utf-8 -*-
{
    'name': 'CRM VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'CRM VTiger Integration',
    'description': """
        CRM VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt Ltd',
    'website': 'https://www.serpentcs.com',
    'category': '',
    'depends': [
        'vtiger_connector_base',
        'crm',
    ],
    'data': [
        'views/crm_view.xml',
    ],
    'installable': True,
}
