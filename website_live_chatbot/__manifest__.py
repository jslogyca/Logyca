# -*- coding: utf-8 -*-
###############################################################################
#
#   website_live_chatbot for Odoo
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Website Live Chatbot',
    'category': 'Website',
    'description': """Geminate comes with feature to smooth your support system with less man power with help of scripted chatbot.
                we provides fully configurable support channel with enable/disable chatbot, private chat, type of communication in related channel with help of category of support and even you can assign as many as operators under channel based on their expertise.
                we are sending complete communication chat history to customers in terms to manage quality of our support system and gethering valuable feedback from them as well""",
    'summary': 'Geminate comes with feature to smooth your support system with less man power with help of scripted chatbot.',
    'author': "Geminate Consultancy Services",
    'company': "Geminate Consultancy Services",
    'website': "https://www.geminatecs.com",
    'license': 'Other proprietary',
    'version': '13.0.0.1',
    'depends': ['multi_chatbot_connector'],
    'data': [
    		 'views/template.xml',
             'views/im_livechat_channel.xml'
            ],
    'images':['static/description/website_live_chatbot.png'],
    'installable': True,
    'auto_install': False,
    'price': 199.00,
    'currency': 'EUR'
}
