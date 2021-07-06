import datetime as dt
import math
import os
import re
from functools import wraps
from typing import List, Tuple, Union, Dict

import requests
from sqlalchemy import distinct
from sqlalchemy.orm import Session
from telegram import (KeyboardButton, ReplyKeyboardMarkup, Update, User, InlineKeyboardMarkup,
                      InlineKeyboardButton)
from telegram.ext import CallbackContext

import bot.messages as messages
import bot.names as nm
from bot.db import get_session
from bot.logger import log
from bot.models import Client, Deal, Item, PriceLimit

MAIN_MENU, DEALS, ITEMS, STATS, TRACKING, NOTIFICATIONS = range(6)
CHANNEL_ID = os.getenv('CHANNEL_ID')

CURRENCY_API_KEY = os.getenv('CURRENCY_API_KEY')


def get_pattern(regex: str) -> re.Pattern:
    return re.compile(regex, re.IGNORECASE)


items_per_page = 8

w_pattern = get_pattern(r'^w\s+[\w\W]+\s+(fn|mw|ft|ww|bs){1}\s*(st|sv)?')
g_pattern = get_pattern(r'^g [\w\W ]+ (fn|mw|ft|ww|bs){1} *$')
c_pattern = get_pattern(r'^c +[\w\W ]+')
k_pattern = get_pattern(r'^k +[\w\W]+ *(fn|mw|ft|ww|bs)? *(st)? *')
s_pattern = get_pattern(r'^s +[\w\W ]+ *$')
p_pattern = get_pattern(r'^p +[\w\W ]+ *$')
a_pattern = get_pattern(r'^a\s+(t|ct)?\s*[\w\W]+')
t_pattern = get_pattern(r'^t +[\w\W ]+')
selected_item_pattern = get_pattern(r'^\d+$')
cp_pattern = get_pattern(r'^\d+\s+\d*(\.|\,)?\d{0,3}')
notify_pattern = get_pattern(r'^\d*(\.|\,)?\d{0,3}$')


def get_tg_user(update: Update) -> User:
    if update.message is not None:
        user: User = update.message.from_user
        log.info(
            f"Client [{user.id} -> @{user.username} -> "
            f"{user.first_name}] send [{update.message.text}]")
    else:
        user: User = update.callback_query.from_user
        log.info(
            f"Client [{user.id} -> @{user.username} -> "
            f"{user.first_name}] send [{update.callback_query.data}]")
        update.callback_query.answer()
    return user


def get_user_lang(user: User) -> str:
    with get_session() as s:
        lang = s.query(Client.lang).filter(Client.chat_id == user.id).scalar()
    return lang


def is_item_limit_reached(user: User, item_name: str, session: Session, lang: str) -> bool:
    # TODO Use client.items
    client_items = [r[0] for r in session.query(distinct(Item.name)).filter(
        Item.client_id == Client.id, Client.chat_id == user.id, Deal.item_id == Item.id,
        Deal.deal_type == 'buy', Deal.closed.is_(False)).all()]
    item_limit = session.query(Client.item_limit).filter(Client.chat_id == user.id).scalar()
    if len(client_items) >= item_limit and item_name not in client_items:
        user.send_message(
            messages.item_limit_reached_message[lang], reply_markup=get_main_menu_inline_markup())
        return True
    else:
        return False


def get_reply_markup(buttons: Union[List, Tuple], rows=1) -> ReplyKeyboardMarkup:
    if not 1 <= rows <= len(buttons):
        raise ValueError('Rows count can not be less than 1 and more than buttons count.')
    cols = math.ceil(len(buttons) / rows)
    last_row_count = len(buttons) - (cols * (rows - 1))
    keyboard = [
        [KeyboardButton(str(buttons[i * cols + j])) for j in range(cols)]
        for i in range(rows - 1)
    ]
    keyboard.append([KeyboardButton(str(b)) for b in buttons[-last_row_count:]])
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_inline_markup(buttons: Union[List, Tuple], rows=1) -> InlineKeyboardMarkup:
    if not 1 <= rows <= len(buttons):
        raise ValueError('Rows count can not be less than 1 and more than buttons count.')
    cols = math.ceil(len(buttons) / rows)
    last_row_count = len(buttons) - (cols * (rows - 1))
    keyboard = [
        [InlineKeyboardButton(str(buttons[i * cols + j]), callback_data=str(buttons[i * cols + j]))
         for j in range(cols)] for i in range(rows - 1)
    ]
    keyboard.append([InlineKeyboardButton(str(b), callback_data=str(b))
                     for b in buttons[-last_row_count:]])
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_inline_markup() -> InlineKeyboardMarkup:
    return get_inline_markup(nm.MAIN_MENU, rows=2)


def get_items_keyboard(user_data: Dict) -> InlineKeyboardMarkup:
    page_num = user_data[nm.PAGE_NUM]
    keyboard = [
        [
            InlineKeyboardButton(f'{i + 1}', callback_data=f'{i}')
            for i in range(len(user_data[nm.PAGES][page_num]))
        ],
        [InlineKeyboardButton('<<<', callback_data='<<<'),
         InlineKeyboardButton('>>>', callback_data='>>>')],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_items_text(user_data: Dict) -> str:
    page_num = user_data[nm.PAGE_NUM]
    page_count = user_data[nm.PAGE_COUNT]
    page = user_data[nm.PAGES][page_num]
    return f'`{page_num + 1}/{page_count}`:\n' + '\n'.join(
        map(lambda x: f'`{x[0] + 1}) {x[1]}`', enumerate(page)))


def get_short_name(item_name: str):
    ret_value = ""
    for key, value in nm.WEAPON_QUALITY.items():
        if value in item_name:
            ret_value = item_name.replace(value, key.upper())
    if nm.ST in ret_value:
        ret_value = ret_value.replace(nm.ST, "ST")
    if nm.SV in ret_value:
        ret_value = ret_value.replace(nm.ST, "SV")
    return ret_value if ret_value else item_name


def is_sub(callback):
    @wraps(callback)
    def inner(update: Update, context: CallbackContext):
        user: User = update.message.from_user
        lang = get_user_lang(user)
        user_status = context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id).status
        if user_status in ('member', 'administrator', 'creator'):
            return callback(update, context)
        else:
            log.info(
                f"Client [{user.id} -> @{user.username} -> {user.first_name}] is not subscriber")
            user.send_message(messages.subscriber_message[lang], disable_web_page_preview=True)

    return inner


def update_price_limits():
    url = (f"http://data.fixer.io/api/latest?access_key={CURRENCY_API_KEY}&"
           f"base=EUR&symbols={','.join(nm.CURRENCY)}")
    try:
        response = requests.get(url, timeout=3).json()
    except requests.RequestException:
        log.exception('Can not receive currency rates from fixer.io')
        return
    except ValueError:
        log.exception('Can not parse response JSON')
        return
    rates: Dict = response.get('rates')
    if rates:
        if rates['USD'] == 0:
            log.info('Can not parse currency rates -> USD rate equals to zero')
            return
        with get_session() as s:
            for currency, rate in rates.items():
                value = round(2000 * rate / rates['USD'], 2)
                price_limit = s.query(PriceLimit).filter(PriceLimit.currency == currency).scalar()
                if price_limit is None:
                    s.add(PriceLimit(currency, value, dt.datetime.now()))
                else:
                    price_limit.value = value
                    price_limit.updated = dt.datetime.now()
        log.info('Price limits update is completed')
