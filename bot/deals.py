import datetime as dt
import re
from typing import List, Tuple, Union, Dict

from sqlalchemy import distinct, update as update_stmt, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from telegram import ReplyKeyboardRemove, Update, User
from telegram.ext import ContextTypes

from bot import messages, constants, utils
from bot.db import Client, Deal, Item, Price
from bot.logger import log


def get_item_function(pattern, pars_func):
    @utils.inject_db_session_and_client
    async def inner(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        session: AsyncSession,
        client: Client,
    ):
        text = re.match(pattern, update.message.text).group()
        text: str = re.sub(r"\s+", " ", text.strip()).lower()
        u_data = context.user_data
        deal_type = u_data[constants.DEAL_TYPE]
        u_data[constants.ITEMS] = {}
        names = await pars_func(text, session)
        u_data[constants.CLIENT_ID] = client.id
        u_data[constants.CLIENT_CURRENCY] = client.currency
        if len(names) < 30:
            put_item_names_into_user_data(names, u_data)
            reply_message = get_items_reply_message(names, text, client.lang, deal_type)
            if len(names) == 1:
                u_data[constants.ITEM_NAME] = names[0]
                if deal_type == "sell":
                    item = await session.scalar(
                        select(Item).filter(
                            Item.name == names[0],
                            Item.client_id == Client.id,
                            Client.chat_id == user.id,
                        )
                    )
                    if item is None:
                        kb = utils.get_inline_markup(("Buy",))
                        await user.send_message(
                            messages.item_price_not_set[client.lang].format(
                                item_name=names[0]
                            ),
                            reply_markup=kb,
                        )
                        return utils.State.DEALS
            await user.send_message(reply_message, reply_markup=ReplyKeyboardRemove())
        else:
            await user.send_message(
                messages.item_error_message[client.lang].format(length=len(names))
            )
        return utils.State.ITEMS

    return inner


@utils.inject_db_session_and_client
async def selected_item(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    u_data = context.user_data
    deal_type = u_data[constants.DEAL_TYPE]
    text = re.match(utils.selected_item_pattern, update.message.text).group()
    try:
        item_name = u_data[constants.ITEMS][int(text)]
    except KeyError as e:
        # if at least one item was added in user_data
        if 1 in u_data[constants.ITEMS]:
            log.info(f"Key [{e}] not found in user_data")
            await user.send_message(messages.select_item_error_message[client.lang])
        else:
            log.info(f"User [{user.id} -> {user.first_name}] do not query any items.")
            await user.send_message(messages.select_item_skip_message[client.lang])
    else:
        u_data[constants.ITEM_NAME] = item_name
        item = await session.scalar(
            select(Item).filter(
                Item.name == u_data[constants.ITEM_NAME],
                Item.client_id == Client.id,
                Client.chat_id == user.id,
            )
        )
        # if user try to add 'sell'-deal without 'buy'-deal with current item
        if deal_type == "sell":
            if item is None:
                kb = utils.get_inline_markup(("Buy",))
                await user.send_message(
                    messages.item_price_not_set[client.lang].format(
                        item_name=u_data[constants.ITEM_NAME]
                    ),
                    reply_markup=kb,
                )
                return utils.State.DEALS
            else:
                currencies = (
                    await session.scalars(
                        select(distinct(Deal.deal_currency)).filter(
                            Deal.item_id == Item.id,
                            Deal.client_id == Client.id,
                            Client.chat_id == user.id,
                            Item.name == u_data[constants.ITEM_NAME],
                            Deal.closed.is_(False),
                        )
                    )
                ).all()

                # user try to add a 'sell'-deal with a currency that is not on the item
                if u_data[constants.CLIENT_CURRENCY] not in currencies:
                    comma_currencies = ",".join(currencies)
                    or_ = " или " if client.lang == "RU" else " or "
                    or_currencies = or_.join(currencies)

                    await user.send_message(
                        messages.wrong_currency_message[client.lang].format(
                            currency=u_data[constants.CLIENT_CURRENCY],
                            or_currencies=or_currencies,
                            comma_currencies=comma_currencies,
                            item_name=u_data[constants.ITEM_NAME],
                        ),
                        reply_markup=utils.get_inline_markup(constants.DEAL_TYPES),
                    )
                    return utils.State.DEALS
        u_data[constants.CLIENT_ID] = client.id
        u_data[constants.CLIENT_CURRENCY] = client.currency
        await user.send_message(
            messages.item_price_count_stage[client.lang].format(
                item_name=item_name, deal_type=deal_type
            ),
            reply_markup=ReplyKeyboardRemove(),
        )

    return utils.State.ITEMS


@utils.inject_db_session_and_client
async def set_deal_type(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    u_data = context.user_data
    deal_type = query.data.lower()
    u_data[constants.DEAL_TYPE] = deal_type
    if constants.ITEM_NAME in u_data:
        await query.edit_message_text(
            messages.item_price_count_stage[client.lang].format(
                item_name=u_data[constants.ITEM_NAME], deal_type=deal_type
            )
        )
    else:
        await query.edit_message_text(messages.query_message[client.lang])
    return utils.State.ITEMS


@utils.inject_db_session_and_client
async def item_count_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    u_data = context.user_data
    if constants.ITEM_NAME not in u_data:
        await user.send_message(
            messages.item_not_set[client.lang], reply_markup=ReplyKeyboardRemove()
        )
        return utils.State.ITEMS

    text = update.message.text.replace(r",", r".")
    text = re.match(utils.cp_pattern, text).group()
    text = re.sub(r"\s+", " ", text.strip()).lower()
    words = text.split()

    count, price = int(words[0]), float(words[1])

    count_is_valid, count_message = validate_count(count, client.lang)
    if not count_is_valid:
        await user.send_message(count_message)
        return utils.State.ITEMS

    price = round(price, 2)
    price_is_valid, price_message = validate_price(price, u_data, context, client.lang)
    if not price_is_valid:
        await user.send_message(price_message)
        return utils.State.ITEMS

    # check if client already has that item
    item = await session.scalar(
        select(Item)
        .where(
            Item.name == u_data[constants.ITEM_NAME],
            Item.client_id == client.id,
        )
        .options(selectinload(Item.deals))
    )
    if item is None:
        item = Item(
            client_id=u_data[constants.CLIENT_ID],
            name=u_data[constants.ITEM_NAME],
            count=count,
        )
        session.add(item)
        await session.flush()
        db_price = await session.scalar(
            select(Price.id).filter(
                Price.name == u_data[constants.ITEM_NAME],
                Price.currency == u_data[constants.CLIENT_CURRENCY],
            )
        )
        if db_price is None:
            session.add(
                Price(
                    name=u_data[constants.ITEM_NAME],
                    currency=u_data[constants.CLIENT_CURRENCY],
                    price=0.0,
                    updated=dt.datetime.now(),
                )
            )
            await session.flush()
    else:
        if u_data[constants.DEAL_TYPE] == "sell" and count > item.count:
            await user.send_message(
                messages.item_count_error[client.lang].format(
                    count=count,
                    item_name=u_data[constants.ITEM_NAME],
                    item_count=item.count,
                ),
                reply_markup=utils.get_inline_markup(constants.DEAL_TYPES),
            )
            return utils.State.DEALS
        item_count = count if u_data[constants.DEAL_TYPE] == "buy" else -count
        item.count += item_count
    closed = True if item.count == 0 else False
    item_id = item.id
    deal = Deal(
        client_id=u_data[constants.CLIENT_ID],
        item_id=item_id,
        price=price,
        deal_type=u_data[constants.DEAL_TYPE],
        volume=count,
        date=dt.datetime.now(),
        deal_currency=u_data[constants.CLIENT_CURRENCY],
        closed=closed,
    )
    session.add(deal)
    # If the deal is closed, then we close all open deals on this item
    if closed:
        upd_stmt = (
            update_stmt(Deal)
            .where(Deal.item_id == item_id)
            .where(Deal.client_id == client.id)
            .where(Deal.closed.is_(False))
            .values(closed=closed)
        )
        await session.execute(upd_stmt)

    await user.send_message(
        messages.deal_added_message[client.lang].format(
            deal_type=u_data[constants.DEAL_TYPE],
            item_name=u_data[constants.ITEM_NAME],
            price=price,
            currency=u_data[constants.CLIENT_CURRENCY],
            count=count,
        ),
        reply_markup=utils.get_main_menu_inline_markup(),
    )
    context.user_data.clear()

    return utils.State.MAIN_MENU


@utils.inject_db_session_and_client
async def unknown_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    await user.send_message(messages.unknown_query_message[client.lang])

    return utils.State.ITEMS


def get_items_reply_message(
    items: List[str], text: str, lang: str, deal_type: str
) -> str:
    if len(items) > 0:
        if len(items) == 1:
            return messages.item_price_count_stage[lang].format(
                item_name=items[0], deal_type=deal_type
            )
        else:
            head = messages.item_found_picker[lang]
            str_names = "\n".join(f"`{i + 1}) {name}`" for i, name in enumerate(items))
            return f"{head}{str_names}"
    else:
        return messages.item_not_exist[lang].format(text=text)


def put_item_names_into_user_data(names: List[str], user_data: dict):
    user_data[constants.ITEMS].clear()
    if len(names) > 0:
        for idx, item_name in enumerate(names):
            user_data[constants.ITEMS][idx + 1] = item_name


def validate_count(count: int, lang: str) -> Tuple[bool, Union[str, None]]:
    if count <= 0:
        return False, messages.item_count_negative[lang].format(count=count)
    if count >= 99999:
        return False, messages.item_count_limit_reached[lang].format(count=count)
    return True, None


def validate_price(
    price: float, u_data: Dict, context, lang: str
) -> Tuple[bool, Union[str, None]]:
    message = None
    currency = u_data[constants.CLIENT_CURRENCY]
    price_limit = context.bot_data.get("price_limits")[currency]

    if price < 0:
        message = messages.item_price_negative[lang]

    if 0 < price < 0.01:
        message = messages.item_price_too_small[lang]

    if u_data[constants.DEAL_TYPE] == "sell" and price == 0:
        message = messages.item_sell_for_zero[lang].format(currency=currency)

    if price > price_limit:
        message = messages.item_price_too_high[lang].format(
            price_limit=price_limit, currency=currency
        )

    return False if message else True, message
