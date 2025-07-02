# -*- coding: utf-8 -*-
# ############################################################################
#
#     Metclouds Technologies Pvt Ltd
#
#     Copyright (C) 2022-TODAY Metclouds Technologies(<https://metclouds.com>)
#     Author: Metclouds Technologies(<https://metclouds.com>)
#
#     You can modify it under the terms of the GNU LESSER
#     GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#     You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#     (LGPL v3) along with this program.
#     If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

{
    'name': 'Day Wise Product Sales Report',
    'summary': 'Day Wise Product Sales Report',
    'version': '1.0.0',
    'description': """Day Wise Product Sales Report""",    
    'author': 'Metclouds Technologies Pvt Ltd',
    'category': 'Sales',
    'maintainer': 'Metclouds Technologies Pvt Ltd',
    'website': 'https://www.metclouds.com',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/daily_sales_report_wizard.xml',
        'views/menu.xml',
        'report/report_daywise_template.xml',
        'report/report.xml',       
    ],
    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'assets': {
        'web.assets_backend': [
            'mt_daywise_product_sales_report/static/src/js/action_manager.js',
        ],
    },    
}
