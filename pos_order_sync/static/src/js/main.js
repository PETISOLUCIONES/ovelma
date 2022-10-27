/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_order_sync.pos_order_sync', function(require) {
	"use strict";
	var core = require('web.core');
	var _t = core._t;
	var rpc = require('web.rpc');
	var pos_model = require('point_of_sale.models');
	var SuperOrder = pos_model.Order;
	var SuperPosModel = pos_model.PosModel.prototype;
	var QWeb = core.qweb;
    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
	const { useListener } = require('web.custom_hooks');
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');

	pos_model.load_models([{
        model:'pos.session',
		field: ['id', 'name', 'user_id', 'config_id', 'start_at', 'stop_at', 'sequence_number', 'payment_method_ids'],
		domain: function(self){ return [['state','=','opened']]; },
        loaded: function(self,  pos_sessions, tmp){
			var other_config_ids = []
            var other_active_session = [];
			for(var i = 0, len = pos_sessions.length; i < len; i++){
				if(pos_sessions[i].user_id[0] != self.user.id){
					other_config_ids.push(pos_sessions[i].config_id[0])
					other_active_session.push(pos_sessions[i])
				}
				if(pos_sessions[i].user_id[0] == self.user.id){
					self.pos_session = pos_sessions[i]
				}
			}
			self.other_config_ids = other_config_ids
			self.other_active_session = other_active_session;
			self.all_quotes=[]
			if(self.other_active_session){
				return new Promise(function (resolve, reject) {
					rpc.query({
						model: 'pos.config',
						method: 'get_floors',
						args: [{'config': self.config_id,
								'other_config': self.other_config_ids}],
					}).then(function (floors) {
						self.other_floors = floors;
						self.other_floor_ids = []
						self.db.floors_by_id = []
						_.forEach(self.other_floors, function(floor){
							self.other_floor_ids.push(floor.id)
							self.db.floors_by_id[floor.id] = floor;
						})
						resolve();
					});
				});
			}
        }
	},
	],{'after': 'res.users'})

	pos_model.Order = pos_model.Order.extend({
		initialize: function(attributes, options) {
			var self = this;
			self.quote_id = null;
			self.quote_name = '';
			self.created_quote_id = null;
			SuperOrder.prototype.initialize.call(this, attributes, options);
		},
		export_as_JSON: function() {
			var self = this;
			var loaded = SuperOrder.prototype.export_as_JSON.call(this);
			if (self.quote_id != null){
				loaded.quote_id = self.quote_id;
				loaded.quote_name = self.quote_name;
			}
			return loaded;
		}
	});

	pos_model.PosModel = pos_model.PosModel.extend({
		_save_to_server: function (orders, options) {
			var self = this;
			return SuperPosModel._save_to_server.call(this,orders,options).then(function(return_dict){
				_.each(orders, function (order) {
				//------------Code  for POS MULtI SESSION --start-------------------
				$('#quote_history').css('color','rgb(94, 185, 55)');
					if(order.data.quote_id){
						rpc.query({
							model: 'pos.quote',
							method: 'change_state_done',
							args: [{"quote_id": order.data.quote_id}],
						})
					}
					self.db.remove_order(order.id);
				});
				var quote_list =[];
				var result_list_length;
				var all_quotes = self.all_quotes;
				var session_id = self.pos_session.id
				all_quotes.forEach(function(quote){
					quote_list.push(quote.quote_id);
				});
				rpc.query({
					model: 'pos.quote',
					method: 'search_all_record',
					args: [{
							"quote_ids": quote_list,
							"session_id": session_id
						}],
				})
				.then(function(result){
					result_list_length = result.quote_list
					if(result_list_length.length){
						result.quote_list.forEach(function(quote){
							all_quotes.unshift(quote);
						});
					}
					self.all_quotes = all_quotes;
					if(self.all_quotes.length)
						$('#new_quote_notification').css('color','rgb(79, 207, 228)');
					else
						$('#new_quote_notification').css('color','rgb(58, 133, 141)');
					$('.quotation_count').text(self.all_quotes.length);
				});

				//Code  for POS MULtI SESSION --end-
				self.set('failed',false);
				return return_dict;
			});
		}
	});

	// Inherit ReceiptScreen----------------
    const PosResReceiptScreen = (ReceiptScreen) =>
		class extends ReceiptScreen {
			mounted(){
				var self = this;
				super.mounted()
				var all_quotes = self.env.pos.all_quotes;
				var index = null;
				var current_order = self.env.pos.get_order();
				if(current_order.quote_name){
					for (var i=0; i< all_quotes.length ; i++){
						if(all_quotes[i].quote_id == current_order.quote_name){
							index = i;
							break;
						}
					}
				}
				if(index != null)
					all_quotes.splice(index,1);
				self.env.pos.all_quotes = all_quotes;
				if(all_quotes.length == 0)
					$('#new_quote_notification').css('color','rgb(58, 133, 141)');
			}
		}
	Registries.Component.extend(ReceiptScreen, PosResReceiptScreen);

	// gui.Gui=gui.Gui.extend({
	// 	show_screen: function(screen_name,params,refresh,skip_close_popup){
	// 		var self = this;
	// 		SuperGui.show_screen.call(self,screen_name,params,refresh,skip_close_popup);
	// 		if(screen_name && jQuery.inArray(screen_name,['payment','products','clientlist','floors']) >=0){
	// 			$('#save_order_quote').show();
	// 			$('#new_quote_notification').show();
	// 			if(this.get_current_screen() == 'floors'){
	// 				$('#save_order_quote').hide();	
	// 			}
	// 		} else {
	// 			$('#save_order_quote').hide();
	// 			$('#new_quote_notification').hide();
	// 		}
	// 	}
	// });

	// Inherit Chrome----------------
    const PosResChrome = (Chrome) =>
		class extends Chrome {
			click_quote_history(event){
				var self = this;
				rpc.query({
					model: 'pos.quote',
					method: 'load_quote_history',
					args: [{
						'session_id':self.env.pos.pos_session.id
					}],
				})
				.then(function(result){
					self.env.pos.history = result.quote_list
					$('#quote_history').css('color','rgb(94, 185, 55)');
					self.showPopup('QuoteHistoryPopupWidget', {
						qoutes:self.env.pos.history
					});
				})
				.catch(function(unused, event) {
					$("#quote_history").css('color','red');
					self.showPopup('WkErrorNotifyPopopWidget', {
						title: _t('Failed to show quotation history'),
						body: _t('Please make sure you are connected to the network.'),
					});
				});
			}
			click_save_order_quote(event){
				var self = this;
				var current_order = self.env.pos.get_order();
				if (current_order.orderlines.length == 0)
					self.showPopup('WkErrorNotifyPopopWidget',{
						title:_t("Empty order!!!"),
						body:_t("You can't send an empty order, Please add some product(s) in cart.")
					});
				else {
					rpc.query({
						model: 'ir.sequence',
						method: 'next_by_code',
						args: ['pos.quote'],
					})
					.catch(function(unused, event) {
						self.showPopup('WkErrorNotifyPopopWidget', {
							title: _t('Failed To Send Quotation'),
							body: _t('Please make sure you are connected to the network.'),
						});
					})
					.then(function(quote_sequence_id) {
						self.showPopup('SaveAsOrderQuotePopupWidget', { });
						setTimeout(function(){
							$('#quote_note').focus();
							$('#quote_id').text(quote_sequence_id);
						},150);
					});
				}
			}
			mounted(){
				super.mounted();
				$('#new_quote_notification').css('color','rgb(58, 133, 141)');
			}
			click_new_quote_notification(){
				var self = this;
				self.update_new_quote_list();
				setTimeout(function() {
					$('.quotation_count').show();
					$('.fa-shopping-cart').show();
					$('.wk_loading').hide()
					var all_quotes_length = self.env.pos.all_quotes.length;
					if(all_quotes_length == 0){
						$("#order_quote_notification").text("No quote available");
						$("#order_quote_notification").fadeIn();
						setTimeout(function() {
							$("#order_quote_notification").fadeOut();
						}, 2000);
					}
					else if(all_quotes_length == 1){
						var all_pos_orders = self.env.pos.get('orders').models || [];
						let already_loaded = false;
						already_loaded = _.find(all_pos_orders, function(pos_order){
							if(pos_order.quote_name && pos_order.quote_name == self.env.pos.all_quotes[0].quote_id)
								return pos_order;
						});
						if(already_loaded){
							self.showPopup('MyMessagePopup', {
								title: _t('Quotation is already loaded'),
								body: _t("This quotation is already loaded & in progress. Please proceed with Order Reference " + already_loaded.sequence_number)
							});
							return
						}
						var quote_dict = self.env.pos.all_quotes[0];
						var set = false
						if(self.env.pos.config.module_pos_restaurant && self.env.pos.config.floor_ids){
							if(quote_dict.table_json){
								var table_data = JSON.parse(quote_dict.table_json)
								if(table_data){
									var table_id = table_data.table_json[0].table_id
									var floor_id = table_data.table_json[1].floor_id
									if(floor_id && table_id){
										if(self.env.pos.floors_by_id[floor_id]){
											_.each(self.env.pos.floors_by_id[floor_id].table_ids, function(id){
												if(id == table_id){
													set = true
													self.env.pos.set_table(self.env.pos.tables_by_id[id])
													self.env.pos.add_new_order();
													if(set){
														self.set_order(quote_dict);
													}
												}
											})
										}
									}
								}
							}
						}
						if(!set){
							self.env.pos.add_new_order();
							self.set_order(quote_dict);
						}
					} else {
						self.showTempScreen('AllQuotesListScreenWidget');
					}
				},1500);
			}
			set_order(quote_dict){
				var self = this;
				var new_order = self.env.pos.get_order();
				new_order.set_client(self.env.pos.db.get_partner_by_id(quote_dict.partner_id[0]));
				quote_dict.line.forEach(function(line) {
					var orderline = new pos_model.Orderline({}, {
						pos: self.env.pos,
						order: new_order,
						product: self.env.pos.db.get_product_by_id(line.product_id),
					});
					orderline.set_unit_price(line.price_unit);
					orderline.set_discount(line.discount);
					orderline.set_quantity(line.qty,'set line price');
					new_order.add_orderline(orderline);
				});
				new_order.quote_id = quote_dict.quote_obj_id;
				new_order.quote_name = quote_dict.quote_id;
				self.showPopup('QuoteSendPopopWidget',{
					'quote_status':'Order Loaded !!!'
				});
			}
			update_new_quote_list(){
				var self = this;
				var session_id = self.env.pos.pos_session.id
				var quote_list = [];
				self.env.pos.all_quotes.forEach(function(quote){
					quote_list.push(quote.quote_id);
				});
				$('.quotation_count').hide();
				$('.fa-shopping-cart').hide();
				$('.wk_loading').show()
				rpc.query({
					model: 'pos.quote',
					method: 'search_all_record',
					args: [{
						"quote_ids": quote_list,
						"session_id": session_id
					}],
				})
				.then(function(result){
					result.quote_list.forEach(function(quote){
						self.env.pos.all_quotes.unshift(quote);
					});
					if(self.env.pos.all_quotes.length)
						$('#new_quote_notification').css('color','rgb(79, 207, 228)');
					else
						$('#new_quote_notification').css('color','rgb(58, 133, 141)');
					$('.quotation_count').text(self.env.pos.all_quotes.length)
				});
				$('.quotation_count').text(self.env.pos.all_quotes.length)
			}
		};
	Registries.Component.extend(Chrome, PosResChrome);

	// QuoteHistoryPopupWidget
    class QuoteHistoryPopupWidget extends AbstractAwaitablePopup { }
    QuoteHistoryPopupWidget.template = 'QuoteHistoryPopupWidget';
    QuoteHistoryPopupWidget.defaultProps = { title: 'Quotation History', value:'' };
	Registries.Component.add(QuoteHistoryPopupWidget);
	
	// MyMessagePopup
    class MyMessagePopup extends AbstractAwaitablePopup { }
    MyMessagePopup.template = 'MyMessagePopup';
    MyMessagePopup.defaultProps = { title: 'Message', value:'' };
    Registries.Component.add(MyMessagePopup);

	// QuoteSendPopopWidget
	class QuoteSendPopopWidget extends AbstractAwaitablePopup {
		mounted(){
			var self = this;
			super.mounted();
			$('.order_status').show();
			$('#order_sent_status').hide();
			$('.order_status').removeClass('order_done');
			$('.show_tick').hide();
			setTimeout(function(){
				$('.order_status').addClass('order_done');
					$('.show_tick').show();
				$('#order_sent_status').show();
				$('.order_status').css({'border-color':'#5cb85c'})
			},500)
			if(!(self.props && self.props.quote_status)){
				setTimeout(function(){
					self.env.pos.get_order().destroy({
						'reason': 'abandon'
					});
					self.cancel();
					self.showScreen('ProductScreen')
					$('.button.pay').click();
					setTimeout(function(){
						$(".button.back").click();
					},50)
				},1500)
			} else {
				setTimeout(function(){
					self.cancel();
				},1500)
			}
		}
	}
	QuoteSendPopopWidget.template = 'QuoteSendPopopWidget';
	QuoteSendPopopWidget.defaultProps = { title: 'Quotation Saved', value: '' };
	Registries.Component.add(QuoteSendPopopWidget);

	// WkErrorNotifyPopopWidget
    class WkErrorNotifyPopopWidget extends AbstractAwaitablePopup {}
    WkErrorNotifyPopopWidget.template = 'WkErrorNotifyPopopWidget';
    WkErrorNotifyPopopWidget.defaultProps = { title: 'Quotation History', value:'' };
	Registries.Component.add(WkErrorNotifyPopopWidget);

	class AllQuotesListScreenWidget extends PosComponent {
		click_back(event){
			var self = this;
			self.showTempScreen('ClientListScreen')
			setTimeout(function(){
				$(".button.back").click();
			},50)
		}
		render_list(quote_list,input_txt) {
			var new_order_data = [];
			var self = this;
			if (input_txt != undefined && input_txt != '') {
				var search_text = input_txt.toLowerCase()
				for (var i = 0; i < quote_list.length; i++) {
					if (quote_list[i].partner_id[1] == false) {
						quote_list[i].partner_id = [0, '-'];
					}
					if (((quote_list[i].quote_id.toLowerCase()).indexOf(search_text) != -1) ||
					((quote_list[i].from_session_id.toLowerCase()).indexOf(search_text) != -1)
					|| ((quote_list[i].partner_id[1].toLowerCase()).indexOf(search_text) != -1) )  {
						new_order_data = new_order_data.concat(quote_list[i]);
					}
				}
				quote_list = new_order_data;
			}
			var contents = $('.wk-quote-list-contents')[0];
			contents.innerHTML = "";
			quote_list.forEach(function(order){
				var orderline_html = QWeb.render('WkQuoteLine', {
					widget: self.env,
					order: order
				});
				var orderline = document.createElement('tbody');
				orderline.innerHTML = orderline_html;
				orderline = orderline.childNodes[1];
				contents.appendChild(orderline);
			});
		}
        constructor() {
            super(...arguments);
			var self = this;
			setTimeout(function(){

				var quotes = self.env.pos.all_quotes;
				self.render_list(quotes);

				$('.order_search').keyup(function() {
					self.render_list(quotes, this.value);
				});

				$('.wk-quote-list-contents').on('click','.wk-qoute-line',function(event){
					var clicked_quote_id = this.id
					var quote_dict;
					quotes.forEach(function(quote){
						if(quote.quote_id == clicked_quote_id){
							quote_dict = quote;
						}
					});
					let already_loaded = false
					var all_pos_orders = self.env.pos.get('orders').models || [];
					already_loaded = _.find(all_pos_orders, function(pos_order){
						if(pos_order.quote_name && pos_order.quote_name == quote_dict.quote_id)
							return pos_order;
					});
					if(already_loaded){
						self.showPopup('MyMessagePopup', {
							title: _t('Quotation is already loaded & in progress'),
							body: _t("This quotation is already in progress. Please proceed with Order Reference " + already_loaded.sequence_number)
						});
						return
					} else {
						var set = false
						if(self.env.pos.config.module_pos_restaurant && self.env.pos.config.floor_ids){
							if(quote_dict.table_json){
								var table_data = JSON.parse(quote_dict.table_json)
								if(table_data){
									var table_id = table_data.table_json[0].table_id
									var floor_id = table_data.table_json[1].floor_id
									if(floor_id && table_id){
										if(self.env.pos.floors_by_id[floor_id]){
											_.each(self.env.pos.floors_by_id[floor_id].table_ids, function(id){
												if(id == table_id){
													set = true
													self.env.pos.set_table(self.pos.tables_by_id[id])
													self.env.pos.add_new_order();
													if(set)
														self.set_order(quote_dict);
												}
											})
										}
									}
								}
							}
						}
						if(!set){
							if(self.env.pos.get_order().get_screen_data() && self.env.pos.get_order().get_screen_data().name == 'FloorScreen'){
								if(self.env.pos.config.floor_ids.length){
									var table_info = null
									_.each(self.env.pos.config.floor_ids, function(floor_id){
										_.each(self.env.pos.tables_by_id, function(table){
											if(table.floor_id[0] == floor_id){
												if(!table_info){
													table_info = table
												}
											}
										})
									})
									if(table_info){
										self.pos.set_table(table_info);
									}
								}
							}
							self.env.pos.add_new_order();
							var new_order = self.set_order(quote_dict);

							self.showTempScreen('ClientListScreen')
							setTimeout(function(){
								$(".button.back").click();
							},50)
						}	
					}
				});
            }, 200);
		}
		set_order(quote_dict){
			var self = this;
			var new_order = self.env.pos.get_order();
			new_order.set_client(self.env.pos.db.get_partner_by_id(quote_dict.partner_id[0]));
			quote_dict.line.forEach(function(line) {
				var orderline = new pos_model.Orderline({}, {
					pos: self.env.pos,
					order: new_order,
					product: self.env.pos.db.get_product_by_id(line.product_id),
				});
				orderline.set_unit_price(line.price_unit);
				orderline.set_discount(line.discount);
				orderline.set_quantity(line.qty,'set line price');
				new_order.add_orderline(orderline);
			});
			new_order.quote_id = quote_dict.quote_obj_id;
			new_order.quote_name = quote_dict.quote_id;
			self.showPopup('QuoteSendPopopWidget',{
				'quote_status':'Order Loaded !!!'
			});
			return new_order
		}
    }
    AllQuotesListScreenWidget.template = 'AllQuotesListScreenWidget';
	Registries.Component.add(AllQuotesListScreenWidget);

	// SaveAsOrderQuotePopupWidget
	class SaveAsOrderQuotePopupWidget extends AbstractAwaitablePopup { 
		constructor() {
			super(...arguments);
			var self = this;
			useListener('focus', '#quote_note', this.focus_quote_note);
			useListener('focusout', '#quote_note', this.focusout_quote_note);
			self.selected_session_id=null;
		}
		focusout_quote_note(event){
			$('.show_info').hide();
		}
		focus_quote_note(event){
			$('.show_info').hide();
		}
		change_tables(event){
			var self = this;
			var related_tables = []
			var floor_id = $('#wk_change_floor').val();
			var floor = self.env.pos.db.floors_by_id[floor_id]
			$('#wk_change_table option').remove();
			$('.show_info').hide();
			if(floor){
				_.forEach(floor.table_ids, function(table){
					related_tables.push(self.env.pos.tables_by_id[table])
				})
			}

			if(related_tables.length){
				$('#wk_change_table').append("<option value=''> </option>")
				_.each(related_tables, function(table){
					$('#wk_change_table').append("<option value=" + table.id + "> " + table.name + "</option>")
				})
			}
		}
		click_table(event){
			$('.show_info').hide();
		}
		click_select_session(session_id){
			var self = this;
			$('#wk_change_floor option').remove();
			$('#wk_change_table option').remove();
			$("#order_quote_id_input_error").hide();
			$('.show_info').hide();
			$(".select_session").css('background','white')
			self.selected_session_id=session_id;
			if(self.selected_session_id){
				var config_id = null
				_.forEach(self.env.pos.other_active_session, function(other_session){
					if(other_session.id == self.selected_session_id){
						config_id = other_session.config_id[0]
					}
				})
				var floors = []
				var tables = []
				_.forEach(self.env.pos.other_floors, function(floor){
					if(floor.pos_config_id == config_id){
						floors.push(floor)
						_.forEach(floor.table_ids, function(table){
							tables.push(self.env.pos.tables_by_id[table])
						})
					}
				})
				if(floors.length && tables.length){	
					$('#wk_floor_table').show();			
					$('#wk_change_floor option').remove();
					$('#wk_change_table option').remove();
					if(floors.length){
						$('#wk_change_floor').append("<option value=''> </option>")
						_.each(floors, function(floor){
							if(floor.table_ids.length){
								$('#wk_change_floor').append("<option value=" + floor.id + "> " + floor.name + "</option>")
							}
						})
					}
				} else {
					$('#wk_floor_table').hide();
				}
			}
			$("span.select_session[id="+ session_id +" ]").css('background','#6EC89B');
		}
		click_wk_print_and_save() {
			var self = this;
			self.click_wk_save_order_quote(true);
			if(self.selected_session_id){
				if(self.env.pos.config.quotation_print_type == 'pdf'){
					setTimeout(function(){
						self.env.pos.do_action('pos_order_sync.report_quote',{additional_context:{
							active_ids:[self.env.pos.get_order().created_quote_id],
						}});
					},1000)
				}
				else if(self.env.pos.config.quotation_print_type == 'posbox'){
					var order = self.env.pos.get_order();
					var to_session = _.filter(self.env.pos.other_active_session, function(session){
						return (session.id == self.to_session_id)
					});
					var quote = {
						'quote_id':$("#quote_id").text(),
						'from_session': self.env.pos.pos_session.config_id[1],
					}
					if(to_session)
						quote['to_session'] = to_session[0].config_id[1];
					var result =  {
						widget: self.env,
						pos: self.env.pos,
						order: order,
						receipt: order.export_for_printing(),
						orderlines: order.get_orderlines(),
						paymentlines: order.get_paymentlines(),
						quote:quote,
					}
					var receipt = QWeb.render('OrderSyncOrderReceipt',result);
					printResult = self.env.pos.proxy.printer.print_receipt(receipt);
				}
			}
		}
		click_wk_save_order_quote(print_order_quote){
			var self = this;
			var current_order = self.env.pos.get_order();
			var order_vals = {};
			var session_id= self.selected_session_id;
			if(!(session_id)){
				$(".select_session").css("background-color","burlywood");
				setTimeout(function(){
					$(".select_session").css("background-color","");
				},100);
				setTimeout(function(){
					$(".select_session").css("background-color","burlywood");
				},200);
				setTimeout(function(){
					$(".select_session").css("background-color","");
				},300);
				setTimeout(function(){
					$(".select_session").css("background-color","burlywood");
				},400);
				setTimeout(function(){
					$(".select_session").css("background-color","");
				},500);
				return;
			} else {
				if($('#wk_change_floor').val() && !$('#wk_change_table').val()){
					if($('#wk_change_floor').val().length && !$('#wk_change_table').val().length){
						$('.show_info').show();
						return
					}
				}
				order_vals.to_session_id = session_id;
				self.to_session_id = session_id;
				order_vals.date_order = moment(current_order.creation_date).format("YYYY-MM-DD HH:mm:ss");
				order_vals.user_id = self.env.pos.cashier ? self.env.pos.cashier.id : self.env.pos.user.id;
				if (current_order.get_client()){
					order_vals.partner_id = current_order.get_client().id
				}
				order_vals.session_id = self.env.pos.pos_session.id;
				order_vals.pricelist_id = current_order.pricelist.id;
				order_vals.note = $("#quote_note").val();
				order_vals.quote_id = $("#quote_id").text();
				order_vals.amount_total = current_order.get_total_with_tax();
				order_vals.amount_tax = current_order.get_total_tax();
				// order_vals.amount_paid = current_order.get_total_paid();
				// order_vals.amount_return = current_order.get_change();
				if(current_order){
					if($('#wk_change_table').val() && $('#wk_change_floor').val()){
						order_vals.table_json = JSON.stringify({'table_json': [{'table_id': $('#wk_change_table').val()},
																{'floor_id': $('#wk_change_floor').val()}]})
						order_vals.pos_res_info = "Floor : "+ self.env.pos.db.floors_by_id[$('#wk_change_floor').val()].name + " & Table : " + self.env.pos.tables_by_id[$('#wk_change_table').val()].name
					}
				}	
				order_vals.lines = []
				var orderlines = self.env.pos.get_order().get_orderlines();
				orderlines.forEach(function(orderline) {
					var order_line_vals = {};
					order_line_vals.product_id = orderline.product.id;
					order_line_vals.price_unit = orderline.get_unit_display_price();
					order_line_vals.qty = orderline.quantity;
					order_line_vals.discount = orderline.discount;
					order_line_vals.price_subtotal = orderline.get_price_without_tax();
					order_line_vals.price_subtotal_incl = orderline.get_price_with_tax();
					var tax_ids = [];
					orderline.product.taxes_id.forEach(function(tax_id) {
						tax_ids.push(tax_id);
					});
					order_line_vals.quote_tax_ids = tax_ids;
					order_vals.lines.push([0, 0, order_line_vals]);
				});
		
				if ($("#quote_id").text() == '') {
					$('#order_quote_id_input_error').text("No Quote Id Found.");
					$('#order_quote_id_input_error').css("width", "66%");
					$('#order_quote_id_input_error').css("padding-left", "26%");
					$('#order_quote_id_input_error').show();
				} else {
					rpc.query({
						model: 'pos.quote',
						method: 'search_quote',
						args: [{'quotation_id':$("#quote_id").text()}],
					})
					.catch(function(unused, event) {
						self.showPopup('WkErrorNotifyPopopWidget', {
							title: _t('Failed To Save Quotation.'),
							body: _t('Please make sure you are connected to the network.'),
						});
					})
					.then(function(result) {
						if (result != null) {
							$('#order_quote_id_input_error').text("This Quote Id has Already been used.");
							$('#order_quote_id_input_error').css("width", "75%");
							$('#order_quote_id_input_error').css("padding-left", "18%");
							$('#order_quote_id_input_error').show();
						} else {
							rpc.query({
								model: 'pos.quote',
								method: 'create',
								args: [order_vals],
							})
							.catch(function(unused, event) {
								self.showPopup('WkErrorNotifyPopopWidget', {
									title: _t('Failed To Save Quotation'),
									body: _t('Please make sure you are connected to the network.'),
								});
							})
							.then(function(new_quote_id) {
								if (print_order_quote == true)
									self.env.pos.get_order().created_quote_id = new_quote_id;
								self.showPopup('QuoteSendPopopWidget');
							});
						}
					});
					$('.show_info').hide();
				}
			}
		}
	}
	SaveAsOrderQuotePopupWidget.template = 'SaveAsOrderQuotePopupWidget';
	SaveAsOrderQuotePopupWidget.defaultProps = { title: 'Quotation', value:'' };
	Registries.Component.add(SaveAsOrderQuotePopupWidget);
});
