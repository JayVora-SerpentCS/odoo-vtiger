# -*- coding: utf-8 -*-
{
    'name': 'Project VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Project VTiger Integration',
    'description': """
        Project VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': '',
    'depends': [
        'vtiger_connector_partner',
        'project',
    ],
    'data': [
        'views/res_company_view.xml',
        'views/project_view.xml',
    ],
    'installable': True,
}
