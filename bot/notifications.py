import math
import re
from typing import List

from sqlalchemy import desc
from sqlalchemy.orm import Session
from telegram import (ReplyKeyboardRemove, Update)
from telegram.ext import CallbackContext

import bot.messages as messages
import bot.names as nm
import bot.utils as bu
from bot.db import get_session
from bot.logger import log
from bot.models import Client, Item, Deal


def change_page(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    diff = 1 if query.data == '>>>' else -1

    if context.user_data[nm.PAGE_NUM] + 1 >= context.user_data[nm.PAGE_COUNT] and diff == 1:
        context.user_data[nm.PAGE_NUM] = context.user_data[nm.PAGE_COUNT] - 1
        return bu.NOTIFICATIONS
    if context.user_data[nm.PAGE_NUM] - 1 < 0 and diff == -1:
        context.user_data[nm.PAGE_NUM] = 0
        return bu.NOTIFICATIONS

    context.user_data[nm.PAGE_NUM] += diff
    text = f'{messages.page[lang]} {bu.get_items_text(context.user_data)}'
    query.edit_message_text(text, reply_markup=bu.get_items_keyboard(context.user_data))
    return bu.NOTIFICATIONS


def choose_item(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    query = update.callback_query
    item_num = int(query.data)
    page_num = context.user_data[nm.PAGE_NUM]
    item_name = context.user_data[nm.PAGES][page_num][item_num]
    context.user_data[nm.ITEM_NAME] = item_name

    with get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).scalar()
        lang = client.lang
        currency = client.currency
        item = client.items.filter(Item.name == item_name).scalar()
        item_deals = item.deals.filter(Deal.deal_type == 'buy').all()
        avg_price = round(sum(map(lambda x: x.price * x.volume, item_deals)) / sum(
            map(lambda x: x.volume, item_deals)), 2)
        context.user_data[nm.AVG_PRICE] = avg_price
        context.user_data[nm.CLIENT_CURRENCY] = currency

    user.bot.delete_message(user.id, query.message.message_id)
    text = messages.notify_item_choose[lang].format(item_name=item_name, currency=currency,
                                                    avg_price=avg_price)
    user.send_message(text, reply_markup=bu.get_inline_markup(['Cancel']))
    return bu.NOTIFICATIONS


def cancel(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    try:
        del context.user_data[nm.ITEM_NAME]
    except KeyError:
        log.info('Key "item_name" does not exist in context.user_data')

    query.edit_message_text(text=f'{messages.page[lang]} {bu.get_items_text(context.user_data)}',
                            reply_markup=bu.get_items_keyboard(context.user_data))
    return bu.NOTIFICATIONS


def show_items(update: Update, context: CallbackContext, session: Session,
               items: List = None):
    user = bu.get_tg_user(update)
    query = update.callback_query
    client = session.query(Client).filter(Client.chat_id == user.id).scalar()
    lang = client.lang

    # TODO
    if query.data == nm.NOTIFY_TYPES[1]:
        query.edit_message_text(text=f'{messages.stop_loss_not_implemented[lang]}\n\n'
                                     f'{messages.menu_message[lang]}',
                                reply_markup=bu.get_main_menu_inline_markup())
        return bu.MAIN_MENU

    if items is None:
        items = [
            item.name for item in
            client.items.filter(Item.count > 0).order_by(desc(Item.updated)).all()
        ]
        if not items:
            query.edit_message_text(messages.no_items[lang],
                                    reply_markup=bu.get_main_menu_inline_markup())
            return bu.MAIN_MENU

    item_count = len(items)
    context.user_data[nm.PAGE_COUNT] = math.ceil(item_count / bu.items_per_page)
    context.user_data[nm.ITEM_COUNT] = item_count
    context.user_data[nm.PAGE_NUM] = 0
    context.user_data[nm.PAGES] = [
        items[i:i + bu.items_per_page] for i in range(0, item_count, bu.items_per_page)
    ]

    query.edit_message_text(text=f'{messages.page[lang]} {bu.get_items_text(context.user_data)}',
                            reply_markup=bu.get_items_keyboard(context.user_data))


def show_items_notify(update: Update, context: CallbackContext):
    with get_session() as session:
        state = show_items(update, context, session)
    return state if state is not None else bu.NOTIFICATIONS


def take_profit(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    if nm.ITEM_NAME not in context.user_data:
        user.send_message(messages.notify_item_not_choose[lang], reply_markup=ReplyKeyboardRemove())
        return bu.NOTIFICATIONS

    item_price = update.message.text.replace(r',', r'.')
    item_price = re.match(bu.notify_pattern, item_price).group()
    item_price = float(item_price)
    if item_price <= context.user_data[nm.AVG_PRICE]:
        user.send_message(messages.notify_take_profit_invalid[lang],
                          reply_markup=ReplyKeyboardRemove())
        return bu.NOTIFICATIONS

    with get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).scalar()
        item = client.items.filter(Item.name == context.user_data[nm.ITEM_NAME]).scalar()
        item.take_profit = item_price
        item.profit_notify = True

    m = messages.notify_take_profit_set[lang].format(price=item_price,
                                                     item_name=context.user_data[nm.ITEM_NAME],
                                                     currency=context.user_data[nm.CLIENT_CURRENCY])
    user.send_message(m, reply_markup=bu.get_main_menu_inline_markup())
    return bu.MAIN_MENU
