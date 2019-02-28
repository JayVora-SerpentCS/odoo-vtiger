# -*- coding: utf-8 -*-
{
    'name': 'Partner VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Partner VTiger Integration',
    'description': """
        Partner VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': 'Sales',
    'depends': [
        'vtiger_connector_base',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
}
