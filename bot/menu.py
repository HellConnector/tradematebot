from sqlalchemy import distinct
from telegram import Update
from telegram.ext import CallbackContext

import bot.messages as messages
import bot.names as nm
import bot.utils as bu
from bot.db import get_session
from bot.models import Client, Deal, Item


def deals(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    query.edit_message_text(messages.deal_type_message[lang],
                            reply_markup=bu.get_inline_markup(nm.DEAL_TYPES))
    context.user_data.clear()
    return bu.DEALS


def stats(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    query = update.callback_query
    with get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).first()
        sell_count = s.query(Deal.id).filter(
            Deal.client_id == client.id, Deal.deal_type == 'sell').count()
        if sell_count == 0:
            query.edit_message_text(messages.stats_is_empty[client.lang],
                                    reply_markup=bu.get_main_menu_inline_markup())
            return bu.MAIN_MENU
        else:
            buttons = ('Newest', '%', 'Value')
            query.edit_message_text(messages.sort_stats_key_message[client.lang],
                                    reply_markup=bu.get_inline_markup(buttons=buttons))
        return bu.STATS


def tracking(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    query = update.callback_query
    with get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).first()
        item_count = s.query(distinct(Item.name)).filter(
            Item.client_id == client.id, Deal.item_id == Item.id, Deal.closed.is_(False),
            Deal.deal_type == 'buy').count()
        if item_count == 0:
            query.edit_message_text(messages.tracking_is_empty[client.lang],
                                    reply_markup=bu.get_main_menu_inline_markup())
            return bu.MAIN_MENU
        else:
            buttons = ('%', 'Value')
            query.edit_message_text(messages.sort_key_message[client.lang],
                                    reply_markup=bu.get_inline_markup(buttons=buttons))
        return bu.TRACKING


def notifications(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    query.edit_message_text(messages.notify_type_choose[lang],
                            reply_markup=bu.get_inline_markup(nm.NOTIFY_TYPES))
    context.user_data.clear()
    return bu.NOTIFICATIONS
