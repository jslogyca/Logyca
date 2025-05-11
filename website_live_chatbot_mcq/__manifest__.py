# -*- coding: utf-8 -*-
###############################################################################
#
#   website_live_helpdesk for Odoo
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
    'name': 'Website Live Chatbot MCQ',
    'category': 'Website',
    'description': """Geminate comes with feature to smooth your support system with less man power with help of scripted chatbot. it supports MCQ (Multiple Choice, Single Answer) type of questions which reduce effort of customer to key in long explanation and allows us to collect accurate information from them. you can configure multiple choice answers in Text OR Image OR Image + Text format which provide excellent appearance for your customer. it is more facilitate the mechanism of survey scheme.""",
    'summary': 'Geminate comes with feature to smooth your support system with less man power with help of scripted chatbot and MCQ flow.',
    'author': "Geminate Consultancy Services",
    'company': "Geminate Consultancy Services",
    'website': "https://www.geminatecs.com",
    'version': '17.0.0.1',
    'license': 'Other proprietary',
    'depends': ['website_live_chatbot'],
    'data': [
                'security/ir.model.access.csv',
                'views/mail_shortcode_views.xml',
                'views/im_livechat_channel.xml',
                'views/assets.xml',
            ],
    'images': ['static/description/website_live_chatbot_mcq.png'],
    'installable': True,
    'auto_install': False,
    'price': 199.00,
    'currency': 'EUR'
}
