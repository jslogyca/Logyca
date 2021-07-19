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
from odoo.addons.website_live_chatbot.controllers.main import LivechatController
from odoo import http, _
from odoo.http import request,route
import re
from datetime import datetime
from odoo.addons.mail.controllers.bus import MailChatController

class LivechatMcqController(LivechatController):
    
    @http.route('/get/current/mcq_channel/connector', type='json',website=True, auth='public')
    def get_mcq_channel_connector(self,uuid,**kwargs):
        if not uuid:
            return False
        channel = request.env['mail.channel'].sudo().search([('uuid', '=', uuid)], limit=1)
        if not channel:
            return False
        mail_channel = channel.livechat_channel_id if channel.livechat_channel_id else False
        if not mail_channel:
            return False
        if not mail_channel.multi_chatbot:
            return False
        if mail_channel.multi_chatbot == 'scripted_bot' and mail_channel.is_mcq_channel:
            return 'is_mcq_channel'
        return False
    
    @http.route('/get/current/options/mcq_channel/connector', type='json',website=True, auth='public')
    def get_current_mcqoptions_chatbot_connector(self,uuid,**kwargs):
        if not uuid:
            return False
        mail_channel = request.env['im_livechat.channel'].sudo().search([('id', '=', uuid)],limit=1)
        if not mail_channel:
            return False
        if not mail_channel.multi_chatbot:
            return False
        if mail_channel.multi_chatbot == 'scripted_bot' and mail_channel.is_mcq_channel:
            return 'is_mcq_channel'
        return False
    
    @http.route('/check_and_end_survey',type='json', auth = 'public', website=True)
    def check_and_survey(self,**kwargs):
        channel = request.env['mail.channel'].sudo().search([('id', '=', kwargs.get('livechat_id'))], limit=1)
        channel.write({"mcq_questions_ended":True})
        helpdesk_id = request.env['online.helpdesk'].sudo().search([('maill_channel_id','=',channel.id)])
        if helpdesk_id:
            helpdesk_id.write({'status':'finish'})
        return channel.mcq_questions_ended
    
    @http.route('/get/current_user',type='json', auth = 'public', website = True)
    def get_current_user(self,**kwargs):
        return request.env.user.partner_id.id
    
    @http.route('/check/mcq_questions_ended',type='json', auth = 'public', website = True)
    def check_mcq_questions_ended(self,**kwargs):
        channel = request.env['mail.channel'].sudo().search([('id', '=', kwargs.get('channel_id'))], limit=1)
        return channel.mcq_questions_ended
        
    @http.route('/stop/mcq_message',type='json', auth = 'public', website = True)
    def stop_mcq_chat(self,**kwargs):
        Message = request.env['mail.message']
        mail_message_ids = kwargs.get('all_messages')
        mail_messages = Message.sudo().browse(mail_message_ids)
        for mes in mail_messages:
            #Remove Submit button completed questions
            current_message_id_replace = mes.body 
            submit_button_substring = current_message_id_replace.split('<button class="btn btn-primary submit_answer_to_bot"')
            if len(submit_button_substring) > 1:
                current_message_id_replace = current_message_id_replace.replace('value=','disabled value=')
                current_message_id_replace = current_message_id_replace.replace('<button class="btn btn-primary submit_answer_to_bot"',"")
                current_message_id_replace = current_message_id_replace.replace(submit_button_substring[1],"")
                #Replace message body
                mes.write({'body' : current_message_id_replace + '<p>Website Live ChatBot MCQ Questions</p>'})
    
    @http.route('/post/mcq_message', type="json", auth='public', website=True)
    def mcq_bot_chat(self,**kwargs):
        Message = request.env['mail.message']
        message = kwargs['message'].get('content', False) if 'message' in kwargs and 'content' in kwargs['message'] else False
        uuid = kwargs.get('uuid', False)
        channel = request.env['mail.channel'].sudo().search([('uuid', '=', uuid)], limit=1)
        channel_id = channel.livechat_channel_id if channel.livechat_channel_id else False
        question_id = kwargs.get('question').split('question_')[1]
        question_val = request.env['mail.shortcode'].sudo().browse(int(question_id))
        answer_id = int(kwargs.get('answer_id'))
        answer_val = request.env['mail.shortcode.radio.answers'].sudo().browse(answer_id)
        current_message_id = Message.sudo().browse(kwargs.get('message_id',0))
        #Add Disabled and Selected radio code for all the radio button
        current_message_id_replace = current_message_id.body.replace('value="' + str(answer_id) + '"', 'value="' + str(answer_id) + '" checked')
        current_message_id_replace = current_message_id_replace.replace('value=','disabled value=')
        
        #Remove Submit button completed questions
        submit_button_substring = current_message_id_replace.split('<button class="btn btn-primary submit_answer_to_bot"')
        if len(submit_button_substring) > 1:
            current_message_id_replace = current_message_id_replace.replace('<button class="btn btn-primary submit_answer_to_bot"',"")
            current_message_id_replace = current_message_id_replace.replace(submit_button_substring[1],"")
        #Replace message body
        current_message_id.write({'body' : current_message_id_replace + '<p>Website Live ChatBot MCQ Questions</p>'})
        if answer_val.next_question_id.radio_answer_ids:
            radio_html = "<p><b>" + str(answer_val.next_question_id.source) + "</b></p><br/><form id='question_" + str(answer_val.next_question_id.id) + "'>"
            now = datetime.now()
            cur_timestamp = datetime.timestamp(now)
            for radio_id in answer_val.next_question_id.radio_answer_ids:
                if radio_id.answer_id.representation == 'text_image':
                    radio_html += '<label class="radio-inline col-6" style="font-weight:normal;">'
                    radio_html += '<input style="margin-top:-1px;vertical-align:middle;" type="radio" class="channel_chatbot" name="channel_chatbot_' + str(cur_timestamp) + '" value="' + str(radio_id.id) + '">'
                    radio_html += " " + radio_id.answer_id.name
                    radio_html += '</label>'
                    radio_html += '<img class="col-6" src="data:image/png;base64,' + radio_id.answer_id.image.decode('utf-8') + '" style="width:100px;padding:3%;"/>'
                elif radio_id.answer_id.representation == 'text':
                    radio_html += '<label class="radio-inline col-12" style="font-weight:normal;">'
                    radio_html += '<input style="margin-top:-1px;vertical-align:middle;" type="radio" class="channel_chatbot" name="channel_chatbot_' + str(cur_timestamp) + '" value="' + str(radio_id.id) + '">'
                    radio_html += " " + radio_id.answer_id.name
                    radio_html += '</label>'
                else:
                    radio_html += '<label class="radio-inline col-6" style="font-weight:normal;">'
                    radio_html += '<input style="margin-top:-1px;vertical-align:middle;" type="radio" class="channel_chatbot" name="channel_chatbot_' + str(cur_timestamp) + '" value="' + str(radio_id.id) + '">'
                    radio_html += '</label>'
                    radio_html += '<img class="col-6" src="data:image/png;base64,' + radio_id.answer_id.image.decode('utf-8') + '" style="width:100px;padding:3%;"/>'
            msg = radio_html + '</form><button class="btn btn-primary submit_answer_to_bot" id ="' + str(cur_timestamp) + '"> Submit</button>' + '<p>Website Live ChatBot MCQ Questions</p>'
            author_id = request.env['res.partner'].sudo().browse(int(2))
            mes_ex = Message.sudo().with_context(do_not_remve_form_tags=True).create({'body':msg,
                        'channel_ids':[(6, 0, [channel.id])],
                        'record_name': 'USER BOT',
                        'author_id':author_id.id,
                        'message_type':'comment',
                        'model':'mail.channel',
                        'res_id':channel.id,
                        })
            mes_ex.attachment_ids = False
        elif answer_val.is_end_of_mcq:
            if answer_val.end_of_mcq_message:
                msg = '<p>' + answer_val.end_of_mcq_message +'</p>'
            else:
                msg = '<p>¡Hasta pronto! gracias por comunicarse con soporte.</p>'
            author_id = request.env['res.partner'].sudo().browse(int(2))
            mes_ex = Message.sudo().with_context(do_not_remve_form_tags=True).create({'body':msg,
                        'channel_ids':[(6, 0, [channel.id])],
                        'record_name': 'USER BOT',
                        'author_id':author_id.id,
                        'message_type':'comment',
                        'model':'mail.channel',
                        'res_id':channel.id,
                        })
            
            if mes_ex:
                if mes_ex.author_id:
                    mes_ex.update({'email_from':mes_ex.author_id.email_formatted})
            
            channel.write({'mcq_questions_ended':True})
            return {'success' : True,'end_of_mcq':True,'current_user':request.env.user.id}
        else:
            msg = '<p>End of Chat. Thanks for replying our questions!</p>'
            author_id = request.env['res.partner'].sudo().browse(int(2))
            mes_ex = Message.sudo().with_context(do_not_remve_form_tags=True).create({'body':msg,
                        'channel_ids':[(6, 0, [channel.id])],
                        'record_name': 'USER BOT',
                        'author_id':author_id.id,
                        'message_type':'comment',
                        'model':'mail.channel',
                        'res_id':channel.id,
                        })
        
        if mes_ex:
            if mes_ex.author_id:
                mes_ex.update({'email_from':mes_ex.author_id.email_formatted})
                
        return {'success' : True,'current_user':request.env.user.id}
    
    @http.route('/pos_message/bot_chat', type="json", auth='public', website=True)
    def bot_chat(self, mail_chat=None, **kwargs):
        ConfigOBJ = request.env['ir.config_parameter'].sudo().get_param('multi_chatbot_connector.is_chain_of_bot')
        Message = request.env['mail.message']
        message = kwargs['message'].get('content', False) if 'message' in kwargs and 'content' in kwargs['message'] else False
        uuid = kwargs.get('uuid', False)
        waiting = kwargs.get('waiting', False)
        msg = ''
        is_welcome_message = kwargs.get('is_welcome_message', False)
        channel = request.env['mail.channel'].sudo().search([('uuid', '=', uuid)], limit=1)
        channel_id = channel.livechat_channel_id if channel.livechat_channel_id else False
        shortcode_obj = request.env['mail.shortcode'].sudo().search([])
        shortcode = False
        if channel_id.multi_chatbot == 'scripted_bot' and not is_welcome_message:
            for code_id in shortcode_obj:
                is_shortcode = str(message.lower()).find(code_id.source.lower())
                if is_shortcode != -1:
                    shortcode = code_id.substitution
        if waiting and channel_id.multi_chatbot == 'scripted_bot':
            msg = "<p>" + str(channel_id.default_message) + "</p>" if channel_id.default_message else "<p> Hello, How Are You!</p>"
            mes_ex = Message.sudo().create({'body':msg,
                            'channel_ids':[(6, 0, [channel.id])],
                            'record_name': 'USER BOT',
                            'message_type':'comment',
                            'model':'mail.channel',
                            'res_id':channel.id
                            })
        
        if not shortcode and ConfigOBJ and channel.helpdesk_lead_id.status in ['new'] and not is_welcome_message:
            c_company = request.env.user.company_id
            chain_list = []
            for line in c_company.chain_of_bots:
                if line.chatbot and line.chatbot != channel_id.multi_chatbot:
                    chain_list.append(line.sequence)
            chain_list.sort()
            for sequence in chain_list:
                chain_bot_id = request.env['chain.bots'].sudo().search([('company_id','=',c_company.id),('sequence','=',sequence)])
                res = getattr(c_company, '%s_chain_response' % str(chain_bot_id.chatbot))(message)
                if res:
                    shortcode = res
                    break
        
        if not shortcode:
            shortcode = channel_id.bot_default_reply
        is_private_bot = True
        available_id = channel_id._get_available_users()
        if channel_id.is_private_bot:
            if request.website.user_id != request.env.user or available_id != request.env.user:
                is_private_bot = False
        if is_welcome_message:
            if channel_id.is_mcq_channel:
                radio_html = "<p><b>" + str(channel_id.source_question_id.source) + "</b></p><br/><form id='question_" + str(channel_id.source_question_id.id) + "'>"
                
                now = datetime.now()
                cur_timestamp = datetime.timestamp(now)
                for radio_id in channel_id.source_question_id.radio_answer_ids:
                    if radio_id.answer_id.representation == 'text_image':
                        radio_html += '<label class="radio-inline col-6" style="font-weight:normal;">'
                        radio_html += '<input style="margin-top:-1px;vertical-align:middle;" type="radio" class="channel_chatbot" name="channel_chatbot_' + str(cur_timestamp) + '" value="' + str(radio_id.id) + '">'
                        radio_html += " " + radio_id.answer_id.name
                        radio_html += '</label>'
                        radio_html += '<img class="col-6" src="data:image/png;base64,' + radio_id.answer_id.image.decode('utf-8') + '" style="width:100px;padding:3%;"/>'
                    elif radio_id.answer_id.representation == 'text':
                        radio_html += '<label class="radio-inline col-12" style="font-weight:normal;">'
                        radio_html += '<input style="margin-top:-1px;vertical-align:middle;" type="radio" class="channel_chatbot" name="channel_chatbot_' + str(cur_timestamp) + '" value="' + str(radio_id.id) + '">'
                        radio_html += " " + radio_id.answer_id.name
                        radio_html += '</label>'
                    else:
                        radio_html += '<label class="radio-inline col-6" style="font-weight:normal;">'
                        radio_html += '<input style="margin-top:-1px;vertical-align:middle;" type="radio" class="channel_chatbot" name="channel_chatbot_' + str(cur_timestamp) + '" value="' + str(radio_id.id) + '">'
                        radio_html += '</label>'
                        radio_html += '<img class="col-6" src="data:image/png;base64,' + radio_id.answer_id.image.decode('utf-8') + '" style="width:100px;padding:3%;"/>'
                    msg = radio_html + '</form><button class="btn btn-primary submit_answer_to_bot" id ="' + str(cur_timestamp) + '"> Submit</button>' + '<p>Website Live ChatBot MCQ Questions</p>'  
            else:
                channel.write({'mcq_questions_ended':True})
                msg = "<p>" + str(message) + "</p>" if message else "<p> Hello, How Are You!</p>"
            
            author_id = request.env['res.partner'].sudo().browse(int(2))
            mes_ex = Message.sudo().with_context(do_not_remve_form_tags=True).create({'body':msg,
                        'channel_ids':[(6, 0, [channel.id])],
                        'record_name': 'USER BOT',
                        'author_id':author_id.id,
                        'message_type':'comment',
                        'model':'mail.channel',
                        'res_id':channel.id,
                        })
            if mes_ex:
                if mes_ex.author_id:
                    mes_ex.update({'email_from':mes_ex.author_id.email_formatted})
            mes_ex.attachment_ids = False
            return {'success' : True,'current_user':request.env.user.id}
        elif shortcode and channel_id and channel_id.multi_chatbot == 'scripted_bot' and is_private_bot and channel.helpdesk_lead_id.status in ['new'] and not waiting:
            author_id = request.env['res.partner'].sudo().browse(int(2))
            mes = Message.sudo().create({'body':'<p>' + str(shortcode) + '</p>',
                            'channel_ids':[(6, 0, [channel.id])],
                            'record_name': 'USER BOT',
                            'author_id':author_id.id,
                            'message_type':'comment',
                            'model':'mail.channel',
                            'res_id':channel.id,
                            })
            if mes:
                if mes.author_id:
                    mes.update({'email_from':mes.author_id.email_formatted})
            return '<p>' + str(shortcode) + '</p>'
        else:
            return False
    
    