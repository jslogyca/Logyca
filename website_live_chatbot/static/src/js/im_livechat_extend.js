odoo.define('website_live_chatbot.im_livechat_extend', function (require) {
	"use strict";
	
	require('bus.BusService');
	var concurrency = require('web.concurrency');
	var config = require('web.config');
	var core = require('web.core');
	var session = require('web.session');
	var time = require('web.time');
	var utils = require('web.utils');
	var Widget = require('web.Widget');
	var Imlivechat = require('im_livechat.im_livechat');
	var rpc = require('web.rpc');
	var WebsiteLivechat = require('im_livechat.model.WebsiteLivechat');
	var WebsiteLivechatMessage = require('im_livechat.model.WebsiteLivechatMessage');
	var WebsiteLivechatWindow = require('im_livechat.WebsiteLivechatWindow');
	var _t = core._t;
	var QWeb = core.qweb;
	// Constants
	var LIVECHAT_COOKIE_HISTORY = 'im_livechat_history';
	var HISTORY_LIMIT = 15;
	var RATING_TO_EMOJI = {
	    "10":"😊",
	    "5":"😐",
	    "1":"😞"
	};
	// History tracking
	var page = window.location.href.replace(/^.*\/\/[^/]+/, '');
	var pageHistory = utils.get_cookie(LIVECHAT_COOKIE_HISTORY);
	var urlHistory = [];
	if (pageHistory) {
	    urlHistory = JSON.parse(pageHistory) || [];
	}
	if (!_.contains(urlHistory, page)) {
	    urlHistory.push(page);
	    while (urlHistory.length > HISTORY_LIMIT) {
	        urlHistory.shift();
	    }
	    utils.set_cookie(LIVECHAT_COOKIE_HISTORY, JSON.stringify(urlHistory), 60*60*24); // 1 day cookie
	}
	
	Imlivechat.LivechatButton.include({
		
		start: function () {
	    	var self = this;
	    	var _super = this._super.bind(this);
	    	if (self._livechat && self._livechat._uuid){
		    	session.rpc('/get/current/chatbot_connector',{uuid: self._livechat._uuid}).then(function(bot_connector){
					self.bot_connector = bot_connector
					return _super();
		    	});
	    	}else if(self.options && self.options.channel_id){
	    		session.rpc('/get/current/options/chatbot_connector',{uuid: self.options.channel_id}).then(function(bot_connector){
					self.bot_connector = bot_connector
					return _super();
		    	});
	    	}else{
	    		return this._super(...arguments);
	    	}
	    },
	    
	    _sendMessage: function (message) {
			var self = this;
			var bot_connector = self.bot_connector
			if(bot_connector == 'scripted_bot'){
				setTimeout(function(){self.re_send_message(message)}, 1500);
				return session.rpc('/mail/chat_post', {uuid: this._livechat.getUUID(), message_content: message.content})
				.then(function () {
					self._chatWindow.scrollToBottom();
				});
			}else{
				
			}
			return this._super(...arguments);
		},
		
		re_send_message: function (message) {
			var self = this;
			session.rpc("/pos_message/bot_chat", {
				message: message,
				uuid: this._livechat._uuid,
				channel_id: this.options.channel_id
			}).then(function(val){
				if(val){
					session.rpc("/mail/chat_history", {
						uuid: self._livechat._uuid,
						limit: 100
						}).then(function (history) {
							self._addMessage(history[1],{});
							self._renderMessages();
							self._addMessage(history[0],{});
							self._renderMessages();
						});
				}else{
					session.rpc("/mail/chat_history", {
						uuid: self._livechat._uuid,
						limit: 100
					}).then(function (history) {
						self._addMessage(history[0],{});
						self._renderMessages();
					});
				}
			});
		},
		
		_openChat: function () {
			var self = this;
			var bot_connector = self.bot_connector
			if(bot_connector == 'scripted_bot' && !self.mcq_bot_connector){
//				setTimeout(function(){
					this.waiting = true;
					self.is_doubled =false;
					if ((this.history) && (this.history.reverse().length > 0)) {
						this.waiting = false;
					}
					var currentpage = window.location.href;
					this.location = true;
					var locationindex = window.location.href.indexOf("/im_livechat/support/");
					if (locationindex > 1) {
						this.location = false;
					}
					if (this._openingChat) {
						return;
					}
					var cookie = utils.get_cookie('im_livechat_session');
					var def;
					this._openingChat = true;
					clearTimeout(this._autoPopupTimeout);
					if (cookie) {
						def = Promise.resolve(JSON.parse(cookie));
					}else if(locationindex > 1  && window.location.href.indexOf('help_id') > 1){
						var helpdesk_id = window.location.href.split("help_id=")[1]
						self.mail_chat = parseInt(helpdesk_id)
						def = rpc.query({
						 	model: 'im_livechat.channel',
			                method: 'get_mail_channel_by_id',
			                args: [,self.mail_chat,self.options.channel_id],
						})
					}else{
						this._messages = []; // re-initialize messages cache
						def = session.rpc('/im_livechat/get_session', {
							channel_id: this.options.channel_id,
							anonymous_name: this.options.default_username,
							previous_operator_id: this._get_previous_operator_id(),
						}, {
							shadow: true
						});
					}
					def.then(function (livechatData) {
						if (!livechatData || !livechatData.operator_pid) {
							alert(_t("None of our collaborators seems to be available, please try again later."));
						} else {
							self._livechat = new WebsiteLivechat({
								parent: self,
								data: livechatData
							});
							self._openChatWindow();
							self.call('bus_service', 'addChannel', self._livechat.getUUID());
							self.call('bus_service', 'startPolling');
							utils.set_cookie('im_livechat_session', JSON.stringify(self._livechat.toData()), 60 * 60);
							utils.set_cookie('im_livechat_auto_popup', JSON.stringify(false), 60 * 60);
						}
					})
//				},200);
			}else{
				return this._super(...arguments);
			}
		},
	    
		_openChatWindow: function () {
			var self = this;
			var bot_connector = self.bot_connector
			if(bot_connector == 'scripted_bot'){
				var self = this;
				if (this.mail_chat) {
					session.rpc("/mail/chat_history", {
						uuid: self._livechat._uuid,
						limit: 100
					}).then(function (history) {
						_.each(history.reverse(), self._addMessage.bind(self));
						self._renderMessages();
					});
				}
				var cookie = utils.get_cookie('im_livechat_session');
				var html = '<div class="container" id="prechatform" >' +
					'<div class="row" >' + ' <div class = "wrapper" > ' +
					'<div class="contact-form-page show-profile" >' +
					'<h5 class="info-chat">Estamos en línea! Por favor diligencia tu información y tu consulta. Te contactaremos lo antes posible para atender tu solicitud.' +
					'<strong>Recuerda que nuestros horarios de atención son de lunes a viernes de 7:00am a 5:00pm.</strong></h5>' +
					'<form>' +
					'<div class="form-group"> ' +
					'<label for="exampleInputText">Nombre Completo</label>' +
					'<input type="text" name="name" id="name" class="form-control" t-att-value="user_id.name" autofocus="autofocus" required="required"/>' +
					'</div>' + ' <div class = "form-group" > ' +
					'<label for="exampleInputEmail1">Correo Electrónico</label>' +
					'<input type="email" name="email" id="email" class="form-control" required="required"/>' +
					'</div>' + '<div class = "form-group" >' +
					'<label for="issue">Categoría:</label>' + ' <select class="form-control" id="category" name="category" required="required">' +
					'<option value="0"> -- Seleccione--  </option>' +
					'</select>' + ' </div>' + ' <div class="form-group" > ' +
					'<label for="exampleInputMessage">Mensaje/Consulta</label>' +
					'<textarea class="form-control" id="note" rows="3" required="required"></textarea>' +
					'</div>' +
					'<span class="btn btn-default submit_buttom">Enviar</span>' +
					'</form> ' + '</div> ' + '</div> ' + '</div> ' + '</div>';
				var waitingscreen = '<div class="container" id="waitingscreen">' +
					'<div class="row">' +
					'<div class="contact-form-page show-profile">' +
					'<h3 class="wait-message"> “Nuestros agentes están ocupados con otro cliente. Te atenderemos en un momento, por favor espera...” </h3>' +
					'<div class="circle">' + '<div class="wave"> </div>' +
					'</div> </div> </div> </div>';
				var options = {
					displayStars: false,
					placeholder: this.options.input_placeholder || "",
				};
				this._chatWindow = new WebsiteLivechatWindow(this, this._livechat, options);
				this._chatWindow.appendTo($('body')).then(function () {
					var cssProps = {bottom: 0};
					cssProps[_t.database.parameters.direction === 'rtl' ? 'left' : 'right'] = 0;
					self._chatWindow.$el.css(cssProps);
					self.$el.hide();
				});
				if ((this.location) && (this.mail_chat === undefined)) {
					this.lead = session.rpc("/check/lead/post", {
							uuid: self._livechat._uuid
						})
						.then(function (res) {
							if (res) {
								self._renderMessages();
							} else {
								self._chatWindow.$el.find('.o_thread_composer').append(html);
								if (session.user_id){
									session.rpc("/user/info", {user_id: session.user_id})
									.then(function(ui){
										if (ui.name!==false){$('#name').val(ui.name)};
										if (ui.email!==false){$('#email').val(ui.email)};
									})
								}
								self._chatWindow.$el.find('.o_composer_text_field').hide();
								self._chatWindow.$el.find('.submit_buttom').on("click", function (ev) {
									var helpdesk_info = {
										'name': $('#name').val(),
										'email': $('#email').val(),
										'note': $('#note').val(),
										'issue_category': $('#category').val(),
									}
									session.rpc("/lead/submit", {
											uuid: self._livechat._uuid,
											helpdesk_info: helpdesk_info
										})
										.then(function (res) {
											if (res) {
												$('#prechatform').remove();
												self._chatWindow.$el.find('.o_composer_text_field').show();
												self._chatWindow.$el.find('.o_thread_composer').append(waitingscreen);
												if (res.timer) {
													setTimeout(function () {
														self.close_waiting_screen(history,res.msg);
														this.waiting = false
													}, parseInt(res.timer));
												}
											} else {
												$.confirm({
													title: 'Lo sentimos! el usuario no está disponible',
													content: 'Por favor seleccione una categoría diferente.',
												});
											}
										});
								});
							}
						});
				} else {
					if ((this.waiting) && (this.mail_chat === undefined)) {
						this._chatWindow.$el.find('.o_thread_composer').append(waitingscreen);
					}
				}
				session.rpc("/isuue/category/", {}).then(function (res) {
					setTimeout(function () {
						_.each(res, function (i, val) {
							$("<option></option>", {
								value: i.id,
								text: i.name
							}).appendTo('#category');
						});
					}, 1000);
				});
			}else{
				return this._super(...arguments);
	    	}
		},
		
		close_waiting_screen: function (history,res_msg) {
			var self = this;
//			this._super(...arguments);
			var _super = this._super.bind(this);
			if (self._livechat && self._livechat._uuid){
		    	session.rpc('/get/current/chatbot_connector',{uuid: self._livechat._uuid}).then(function(bot_connector){
					if(bot_connector == 'scripted_bot'){
						self.bot_connector = bot_connector
						session.rpc("/pos_message/bot_chat", {
							uuid: self._livechat._uuid,
							channel_id: self.options.channel_id,
							message:res_msg,
							is_welcome_message:true,
						}).then(function(msgr){
						session.rpc("/mail/chat_history", {
							uuid: self._livechat._uuid,
							limit: 100
							}).then(function (history) {
								self._addMessage(history[0],{});
								self._renderMessages();
							});
						});
						$('#waitingscreen').remove();
					}else{
						return _super();
					}
		    	});
	    	}else{
	    		return _super();
	    	}
		},
		
		bot_send_message: function () {
			var self = this;
			session.rpc("/pos_message/bot_chat", {
				uuid: self._livechat._uuid,
				channel_id: self.options.channel_id,
				waiting: true
			});
		},
		
	    _handleNotification: function  (notification){
	    	var self = this;
			var bot_connector = self.bot_connector
	    	if(bot_connector == 'scripted_bot'){
		    	var locationindex = window.location.href.indexOf("/im_livechat/support/");
		    	if(locationindex >1){
		    		var is_sent = false;
		    		this.is_doubled = true;
		    		if(this._livechat && notification[1].body){
		    			_.each(this._messages,function(key){
		    				if(key._id == notification[1].id){
		    					is_sent = true;
		    				}
		    			});
		            	if(!is_sent){
		    				this._addMessage(notification[1]);
			                this._renderMessages();
			                if (this._chatWindow.isFolded() || !this._chatWindow.isAtBottom()) {
			                    this._livechat.incrementUnreadCounter();
			                }
		            	}
		            }
		    	}else{
			        if (this._livechat && (notification[0] === this._livechat.getUUID())) {
			            if (notification[1]._type === 'history_command') { // history request
			                var cookie = utils.get_cookie(LIVECHAT_COOKIE_HISTORY);
			                var history = cookie ? JSON.parse(cookie) : [];
			                session.rpc('/im_livechat/history', {
			                    pid: this._livechat.getOperatorPID()[0],
			                    channel_uuid: this._livechat.getUUID(),
			                    page_history: history,
			                });
			            } else if (notification[1].info === 'typing_status') {
			                var isWebsiteUser = notification[1].is_website_user;
			                if (isWebsiteUser) {
			                    return; // do not handle typing status notification of myself
			                }
			                var partnerID = notification[1].partner_id;
			                if (notification[1].is_typing) {
			                    this._livechat.registerTyping({ partnerID: partnerID });
			                } else {
			                    this._livechat.unregisterTyping({ partnerID: partnerID });
			                }
			            } else { // normal message
			                this._addMessage(notification[1]);
			                this._renderMessages();
			                if (this._chatWindow.isFolded() || !this._chatWindow.isAtBottom()) {
			                    this._livechat.incrementUnreadCounter();
			                }
			            }
			        }
		    	}
	    	}else{
	    		return this._super(...arguments);
	    	}
	    },
	});
});