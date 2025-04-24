import math
import re

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from telegram import ReplyKeyboardRemove, Update, User
from telegram.ext import ContextTypes

from bot import messages, constants, utils
from bot.db import Client, Item
from bot.logger import log


@utils.inject_db_session_and_client
async def change_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    diff = 1 if query.data == ">>>" else -1

    if (
        context.user_data[constants.PAGE_NUM] + 1
        >= context.user_data[constants.PAGE_COUNT]
        and diff == 1
    ):
        context.user_data[constants.PAGE_NUM] = (
            context.user_data[constants.PAGE_COUNT] - 1
        )
        return utils.State.NOTIFICATIONS
    if context.user_data[constants.PAGE_NUM] - 1 < 0 and diff == -1:
        context.user_data[constants.PAGE_NUM] = 0
        return utils.State.NOTIFICATIONS

    context.user_data[constants.PAGE_NUM] += diff
    text = f"{messages.page[client.lang]} {utils.get_items_text(context.user_data)}"
    await query.edit_message_text(
        text, reply_markup=utils.get_items_keyboard(context.user_data)
    )
    return utils.State.NOTIFICATIONS


@utils.inject_db_session_and_client
async def choose_item(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    item_num = int(query.data)
    page_num = context.user_data[constants.PAGE_NUM]
    item_name = context.user_data[constants.PAGES][page_num][item_num]
    context.user_data[constants.ITEM_NAME] = item_name

    currency = client.currency
    item: Item = await session.scalar(
        client.items.select()
        .where(Item.name == item_name)
        .options(selectinload(Item.deals))
    )

    avg_price = round(
        sum(map(lambda x: x.price * x.volume, item.deals))
        / sum(map(lambda x: x.volume, item.deals)),
        2,
    )
    context.user_data[constants.AVG_PRICE] = avg_price
    context.user_data[constants.CLIENT_CURRENCY] = currency

    await query.delete_message()
    text = messages.notify_item_choose[client.lang].format(
        item_name=item_name, currency=currency, avg_price=avg_price
    )
    await user.send_message(
        text, reply_markup=utils.get_inline_markup(["Cancel"])
    )
    return utils.State.NOTIFICATIONS


@utils.inject_db_session_and_client
async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    try:
        del context.user_data[constants.ITEM_NAME]
    except KeyError:
        log.info('Key "item_name" does not exist in context.user_data')

    await query.edit_message_text(
        text=f"{messages.page[client.lang]} {utils.get_items_text(context.user_data)}",
        reply_markup=utils.get_items_keyboard(context.user_data),
    )
    return utils.State.NOTIFICATIONS


@utils.inject_db_session_and_client
async def show_items(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query

    # TODO Implement Stop Loss notifications
    if query.data == constants.NOTIFY_TYPES[1]:
        await query.edit_message_text(
            text=f"{messages.stop_loss_not_implemented[client.lang]}\n\n"
            f"{messages.menu_message[client.lang]}",
            reply_markup=utils.get_main_menu_inline_markup(),
        )
        return utils.State.MAIN_MENU

    items = list(
        map(
            lambda i: i.name,
            (
                await session.scalars(
                    client.items.select()
                    .where(Item.count > 0)
                    .order_by(desc(Item.updated))
                )
            ).all(),
        )
    )

    if not items:
        await query.edit_message_text(
            messages.no_items[client.lang],
            reply_markup=utils.get_main_menu_inline_markup(),
        )
        return utils.State.MAIN_MENU

    item_count = len(items)
    context.user_data[constants.PAGE_COUNT] = math.ceil(
        item_count / utils.items_per_page
    )
    context.user_data[constants.ITEM_COUNT] = item_count
    context.user_data[constants.PAGE_NUM] = 0
    context.user_data[constants.PAGES] = [
        items[i : i + utils.items_per_page]
        for i in range(0, item_count, utils.items_per_page)
    ]

    await query.edit_message_text(
        text=f"{messages.page[client.lang]} {utils.get_items_text(context.user_data)}",
        reply_markup=utils.get_items_keyboard(context.user_data),
    )

    return utils.State.NOTIFICATIONS


@utils.inject_db_session_and_client
async def take_profit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    if constants.ITEM_NAME not in context.user_data:
        await user.send_message(
            messages.notify_item_not_choose[client.lang],
            reply_markup=ReplyKeyboardRemove(),
        )
        return utils.State.NOTIFICATIONS

    item_price = update.message.text.replace(r",", r".")
    item_price = re.match(utils.notify_pattern, item_price).group()
    item_price = float(item_price)
    if item_price <= context.user_data[constants.AVG_PRICE]:
        await user.send_message(
            messages.notify_take_profit_invalid[client.lang],
            reply_markup=ReplyKeyboardRemove(),
        )
        return utils.State.NOTIFICATIONS

    item = await session.scalar(
        client.items.select().where(
            Item.name == context.user_data[constants.ITEM_NAME]
        )
    )

    item.take_profit = item_price
    item.profit_notify = True

    m = messages.notify_take_profit_set[client.lang].format(
        price=item_price,
        item_name=context.user_data[constants.ITEM_NAME],
        currency=context.user_data[constants.CLIENT_CURRENCY],
    )
    await user.send_message(
        m, reply_markup=utils.get_main_menu_inline_markup()
    )
    return utils.State.MAIN_MENU
