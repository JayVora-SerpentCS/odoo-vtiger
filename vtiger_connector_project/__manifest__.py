# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Project VTiger Integration',
    'version': '10.0.1.0.0',
    'summary': 'Project VTiger Integration',
    'description': """
        Project VTiger Integration""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': 'Project',
    'license': 'AGPL-3',
    'depends': ['project',
                'vtiger_connector_partner'],
    'data': ['views/res_company_view.xml',
             'views/project_view.xml'],
    'installable': True,
}
