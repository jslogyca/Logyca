odoo.define('website_live_chatbot_mcq.im_livechat_extend', function (require) {
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
		    	session.rpc('/get/current/mcq_channel/connector',{uuid: self._livechat._uuid}).then(function(bot_connector){
					self.mcq_bot_connector = bot_connector
					return _super();
		    	});
	    	}else if(self.options && self.options.channel_id){
	    		session.rpc('/get/current/options/mcq_channel/connector',{uuid: self.options.channel_id}).then(function(bot_connector){
					self.bot_connector = bot_connector
					return _super();
		    	});
	    	}else{
	    		return this._super(...arguments);
	    	}
	    },
	    
	    _openChat: function () {
			var self = this;
			if (self.mcq_bot_connector == 'is_mcq_channel'){
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
					if (cookie && locationindex == -1) {
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
							if (locationindex > 1) {
								session.rpc("/check/mcq_questions_ended", {
						    	'channel_id' : self._livechat._id,	
								}).then(function(ended){
									if(ended) {
										self._openChatWindow();
										self.call('bus_service', 'addChannel', self._livechat.getUUID());
										self.call('bus_service', 'startPolling');
							
										utils.set_cookie('im_livechat_session', JSON.stringify(self._livechat.toData()), 60 * 60);
										utils.set_cookie('im_livechat_auto_popup', JSON.stringify(false), 60 * 60);
									}else{
										$('body').append('<div class="notify"><span id="notifyType" class=""></span></div>')
										$(".notify").toggleClass("active");
									    $("#notifyType").toggleClass("success");
									    setTimeout(function(){
									      $(".notify").removeClass("active");
									      $("#notifyType").removeClass("success");
									      $(".notify").remove();
									    },2000);
										self._openingChat = false
										utils.set_cookie('im_livechat_session', JSON.stringify(self._livechat.toData()), 60 * 60);
										return;
									}
								});
							}
							else {
								self._openChatWindow();
								self.call('bus_service', 'addChannel', self._livechat.getUUID());
								self.call('bus_service', 'startPolling');
					
								utils.set_cookie('im_livechat_session', JSON.stringify(self._livechat.toData()), 60 * 60);
								utils.set_cookie('im_livechat_auto_popup', JSON.stringify(false), 60 * 60);
							}
						}
					})
//				},200);
			}else{
				return this._super(...arguments);
			}
		},
		
		close_waiting_screen: function (history,res_msg) {
			var self = this;
//			this._super(...arguments);
			var _super = this._super.bind(this);
			if (self._livechat && self._livechat._uuid){
		    	session.rpc('/get/current/mcq_channel/connector',{uuid: self._livechat._uuid}).then(function(bot_connector){
		    		if(bot_connector == 'is_mcq_channel'){
						self.bot_connector = 'scripted_bot'
						self.mcq_bot_connector = bot_connector
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
		
		_renderMessages: function () {
			if (this.mcq_bot_connector == 'is_mcq_channel'){
		    	var shouldScroll = !this._chatWindow.isFolded() && this._chatWindow.isAtBottom();
		        this._livechat.setMessages(this._messages);
		        this._chatWindow._thread._messages = this._messages;
		        this._chatWindow.render();
		        var self = this;
		        if (shouldScroll) {
		            this._chatWindow.scrollToBottom();
		        }
		        var $lastbutton = $('.submit_answer_to_bot').slice(-1)[0] ;
		        $('.submit_answer_to_bot').hide();
		        session.rpc("/get/current_user", {
	    		}).then(function(user_id){
	    			if(self._livechat._operatorPID[0] != user_id && $($lastbutton).length > 0) {
	    				self._chatWindow._threadWidget.dont_hide_submit = true;
	    				self._chatWindow.$input.prop('disabled',true)
	            		$($lastbutton).show();
	            	}
	            	if(self._livechat._operatorPID[0] != user_id && $($lastbutton).length == 0) {
	            		self._chatWindow.$input.prop('disabled',false)
	            	}
	            	var locationindex = window.location.href.indexOf("/im_livechat/support/");
	    			if (locationindex > 1) {
	    				self._chatWindow.$input.prop('disabled',false)
	    				$($lastbutton).hide();
	    			}
	        	})
		        
				var latest_message = self._messages.slice(-1)[0];
				if($($lastbutton).length > 0 && latest_message._serverAuthorID[0] != 2) {
	        		var message_ids = [];
	        		_.each(self._messages,function(key){
	        			message_ids.push(key._id);
	        		})
	        		session.rpc("/stop/mcq_message", {
	        			all_messages : message_ids
	        		}).then(function(){
	        			session.rpc("/mail/chat_history", {
							uuid: self._livechat._uuid,
							limit: 100
							}).then(function (history) {
								self._messages = []
								var history_length = history.length;
								for(var i=history.length-1; i >= 0;i--) {
									self._addMessage(history[i],{});
								}
								self._renderMessages();
							});
	        		})
	        	}
		        
		        $($lastbutton).click(function(){
		        	var selectedvalue = $('input[name="channel_chatbot_' + $(this).attr('id') + '"]:checked').val()
		        	var current_question = $($lastbutton).parent().find("form").attr("id")
		        	if(!selectedvalue) {
		        		$('input[name="channel_chatbot_' + $(this).attr('id') + '"]').focus()
		        	}else{
		        		session.rpc("/post/mcq_message", {
			        		question : current_question,
			        		answer_id : selectedvalue,
							uuid : self._livechat._uuid,
							channel_id : self.options.channel_id,
							message_id :  self._messages.slice(-1)[0]._id,
						}).then(function(val){
							if(val){
								session.rpc("/mail/chat_history", {
									uuid: self._livechat._uuid,
									limit: 100
								}).then(function (history) {
									self._messages = []
									if (val.end_of_mcq) {
										self.hide_all_submit_buttons = true;
									}
									var history_length = history.length;
									for(var i=history.length-1; i >= 0;i--) {
										self._addMessage(history[i],{});
										self._renderMessages();
										self._chatWindow.$input.keyup()
									}
									self._chatWindow.scrollToBottom();
								});
							}
						});
		        	}
		        })
			}else{
				return this._super(...arguments);
			}
	    },
		
//		_closeChat: function () {
//	    	if (this.mcq_bot_connector == 'is_mcq_channel'){
//	    		utils.set_cookie('im_livechat_session', "", -1); // remove cookie
//	    	}
//	    	return this._super(...arguments);
//	    },
		
	})
})