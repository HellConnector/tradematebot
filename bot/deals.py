import datetime as dt
import re
from typing import Callable, List, Tuple, Union, Dict

from sqlalchemy import Table, distinct, update as update_stmt
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext

import bot.db as db
import bot.messages as messages
import bot.names as nm
import bot.utils as bu
from bot.logger import log
from bot.models import Client, Deal, Item, Price, PriceLimit


def get_item_function(pattern, pars_func) -> Callable[[Update, CallbackContext], int]:
    def inner(update: Update, context: CallbackContext) -> int:
        user = bu.get_tg_user(update)
        text = re.match(pattern, update.message.text).group()  # Обрезаем по шаблону
        text = re.sub(r'\s+', ' ', text.strip()).lower()  # Удаляем ненужные пробелы
        u_data = context.user_data
        deal_type = u_data[nm.DEAL_TYPE]
        u_data[nm.ITEMS] = {}
        with db.get_session() as s:
            names = pars_func(text, s)
            client = s.query(Client).filter(Client.chat_id == user.id).first()
            u_data[nm.CLIENT_ID] = client.id
            u_data[nm.CLIENT_CURRENCY] = client.currency
            if len(names) < 30:
                put_item_names_into_user_data(names, u_data)
                reply_message = get_items_reply_message(names, text, client.lang, deal_type)
                if len(names) == 1:
                    u_data[nm.ITEM_NAME] = names[0]
                    if deal_type == 'buy':
                        if bu.is_item_limit_reached(user, names[0], s, client.lang):
                            return bu.MAIN_MENU
                    else:
                        item = s.query(Item).filter(
                            Item.name == names[0], Item.client_id == Client.id,
                            Client.chat_id == user.id).first()
                        if item is None:
                            kb = bu.get_inline_markup(('Buy',))
                            user.send_message(messages.item_price_not_set[client.lang].format(
                                item_name=names[0]), reply_markup=kb)
                            return bu.DEALS
                user.send_message(reply_message, reply_markup=ReplyKeyboardRemove())
            else:
                user.send_message(
                    messages.item_error_message[client.lang].format(length=len(names)))
        return bu.ITEMS

    return inner


def selected_item(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    u_data = context.user_data
    deal_type = u_data[nm.DEAL_TYPE]
    text = re.match(bu.selected_item_pattern, update.message.text).group()  # Обрезаем по шаблону
    try:
        item_name = u_data[nm.ITEMS][int(text)]
    except KeyError as e:
        # Если хотя бы одна вещь была добавлена в user_data
        if 1 in u_data[nm.ITEMS]:
            log.info(f'Key [{e}] not found in user_data')
            user.send_message(messages.select_item_error_message[lang])
        else:
            log.info(f"User [{user.id} -> {user.first_name}] do not query any items.")
            user.send_message(messages.select_item_skip_message[lang])
    else:
        u_data[nm.ITEM_NAME] = item_name
        with db.get_session() as s:
            client = s.query(Client).filter(Client.chat_id == user.id).scalar()
            item = s.query(Item).filter(
                Item.name == u_data[nm.ITEM_NAME], Item.client_id == Client.id,
                Client.chat_id == user.id).first()
            # При попытке добавить сделку продажи с отсутствующим ещё предметом просим добавить
            # сделку покупки.
            if deal_type == 'sell':
                if item is None:
                    kb = bu.get_inline_markup(('Buy',))
                    user.send_message(messages.item_price_not_set[lang].format(
                        item_name=u_data[nm.ITEM_NAME]), reply_markup=kb)
                    return bu.DEALS
                else:
                    temp_currencies = s.query(distinct(Deal.deal_currency)).filter(
                        Deal.item_id == Item.id, Deal.client_id == Client.id,
                        Client.chat_id == user.id, Item.name == u_data[nm.ITEM_NAME],
                        Deal.closed.is_(False)).all()
                    currencies = [c for c, in temp_currencies]
                    # Попытка добавить сделку продажи с валютой, которой на предмете нет
                    if u_data[nm.CLIENT_CURRENCY] not in currencies:
                        comma_currencies = ','.join(currencies)
                        or_currencies = ' or '.join(currencies) if lang == 'EN' else ' или '.join(
                            currencies)
                        user.send_message(messages.wrong_currency_message[lang].format(
                            currency=u_data[nm.CLIENT_CURRENCY], or_currencies=or_currencies,
                            comma_currencies=comma_currencies, item_name=u_data[nm.ITEM_NAME]),
                            reply_markup=bu.get_inline_markup(nm.DEAL_TYPES))
                        return bu.DEALS
            else:
                if bu.is_item_limit_reached(user, item_name, s, lang):
                    return bu.MAIN_MENU
            u_data[nm.CLIENT_ID] = client.id
            u_data[nm.CLIENT_CURRENCY] = client.currency
            user.send_message(messages.item_price_count_stage[lang].format(
                item_name=item_name, deal_type=deal_type),
                reply_markup=ReplyKeyboardRemove())

    return bu.ITEMS


def set_deal_type(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    u_data = context.user_data
    deal_type = query.data.lower()
    u_data[nm.DEAL_TYPE] = deal_type
    if nm.ITEM_NAME in u_data:
        query.edit_message_text(messages.item_price_count_stage[lang].format(
            item_name=u_data[nm.ITEM_NAME], deal_type=deal_type))
    else:
        query.edit_message_text(messages.query_message[lang])
    return bu.ITEMS


def item_count_price(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    u_data = context.user_data
    if nm.ITEM_NAME not in u_data:
        user.send_message(messages.item_not_set[lang], reply_markup=ReplyKeyboardRemove())
        return bu.ITEMS

    text = update.message.text.replace(r',', r'.')
    text = re.match(bu.cp_pattern, text).group()
    text = re.sub(r'\s+', ' ', text.strip()).lower()
    words = text.split()

    count, price = int(words[0]), float(words[1])

    count_is_valid, count_message = validate_count(count, lang)
    if not count_is_valid:
        user.send_message(count_message)
        return bu.ITEMS

    price = round(price, 2)
    price_is_valid, price_message = validate_price(price, u_data, lang)
    if not price_is_valid:
        user.send_message(price_message)
        return bu.ITEMS

    with db.get_session() as s:
        client_id = s.query(Client.id).filter(Client.chat_id == user.id).first()[0]
        # Проверяем, есть ли предмет с таким названием в таблице Items у этого клиента
        item = s.query(Item).filter(
            Item.name == u_data[nm.ITEM_NAME], Item.client_id == Client.id,
            Client.chat_id == user.id).first()
        if item is None:
            item = Item(client_id=u_data[nm.CLIENT_ID], name=u_data[nm.ITEM_NAME], count=count)
            s.add(item)
            s.commit()
            db_price = s.query(Price.id).filter(
                Price.name == u_data[nm.ITEM_NAME],
                Price.currency == u_data[nm.CLIENT_CURRENCY]).scalar()
            if db_price is None:
                s.add(Price(name=u_data[nm.ITEM_NAME], currency=u_data[nm.CLIENT_CURRENCY],
                            price=0.0, updated=dt.datetime.now()))
                s.commit()
        else:
            if u_data[nm.DEAL_TYPE] == 'sell' and count > item.count:
                user.send_message(
                    messages.item_count_error[lang].format(
                        count=count, item_name=u_data[nm.ITEM_NAME], item_count=item.count),
                    reply_markup=bu.get_inline_markup(nm.DEAL_TYPES))
                return bu.DEALS
            item_count = count if u_data[nm.DEAL_TYPE] == 'buy' else -count
            item.count += item_count
        closed = True if item.count == 0 else False
        item_id = item.id
        deal = Deal(client_id=u_data[nm.CLIENT_ID], item_id=item_id, price=price,
                    deal_type=u_data[nm.DEAL_TYPE], volume=count, date=dt.datetime.now(),
                    deal_currency=u_data[nm.CLIENT_CURRENCY], closed=closed)
        s.add(deal)
    # Если сделка закрывается, то закрываем все открытые сделки по этому предмету
    if closed:
        d_tbl: Table = Deal.__table__
        upd_stmt = update_stmt(d_tbl).where(d_tbl.c.item_id == item_id).where(
            d_tbl.c.client_id == client_id).where(d_tbl.c.closed.is_(False)).values(closed=closed)
        db.engine.execute(upd_stmt)

    user.send_message(messages.deal_added_message[lang].format(
        deal_type=u_data[nm.DEAL_TYPE], item_name=u_data[nm.ITEM_NAME], price=price,
        currency=u_data[nm.CLIENT_CURRENCY], count=count),
        reply_markup=bu.get_main_menu_inline_markup())
    context.user_data.clear()

    return bu.MAIN_MENU


def unknown_query(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    user.send_message(messages.unknown_query_message[lang])

    return bu.ITEMS


def get_items_reply_message(items: List[str], text: str, lang: str, deal_type: str) -> str:
    if len(items) > 0:
        if len(items) == 1:
            return messages.item_price_count_stage[lang].format(
                item_name=items[0], deal_type=deal_type)
        else:
            head = messages.item_found_picker[lang]
            str_names = '\n'.join(f'`{i + 1}) {name}`' for i, name in enumerate(items))
            return f'{head}{str_names}'
    else:
        return messages.item_not_exist[lang].format(text=text)


def put_item_names_into_user_data(names: List[str], user_data: dict):
    user_data[nm.ITEMS].clear()
    if len(names) > 0:
        for idx, item_name in enumerate(names):
            user_data[nm.ITEMS][idx + 1] = item_name


def validate_count(count: int, lang: str) -> Tuple[bool, Union[str, None]]:
    if count <= 0:
        return False, messages.item_count_negative[lang].format(count=count)
    if count >= 99999:
        return False, messages.item_count_limit_reached[lang].format(count=count)
    return True, None


def validate_price(price: float, u_data: Dict, lang: str) -> Tuple[bool, Union[str, None]]:
    message = None
    currency = u_data[nm.CLIENT_CURRENCY]
    with db.get_session() as s:
        price_limit = s.query(PriceLimit.value).filter(PriceLimit.currency == currency).scalar()

    if price < 0:
        message = messages.item_price_negative[lang]

    if 0 < price < 0.01:
        message = messages.item_price_too_small[lang]

    if u_data[nm.DEAL_TYPE] == 'sell' and price == 0:
        message = messages.item_sell_for_zero[lang].format(currency=currency)

    if price > price_limit:
        message = messages.item_price_too_high[lang].format(price_limit=price_limit,
                                                            currency=currency)

    return False if message else True, message
