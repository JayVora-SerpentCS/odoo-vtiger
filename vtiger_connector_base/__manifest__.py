# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name': 'VTiger Base Connector',
    'version': '10.0.1.0.0',
    'summary': 'VTiger Base Connector',
    'description': """
        VTiger Base Connector""",
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'category': 'Base Module',
    'license': 'AGPL-3',
    'depends': ['base'],
    'data': ['data/vtiger_connector_base_data.xml',
             'views/vtiger_templates.xml',
             'views/res_company_view.xml'],
    'installable': True,
}
