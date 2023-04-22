from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from telegram import Update, User
from telegram.ext import ContextTypes

import messages as messages
import constants
import utils
from db import Client, Deal, Item


@utils.inject_db_session_and_client
async def deals(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    await query.edit_message_text(
        messages.deal_type_message[client.lang],
        reply_markup=utils.get_inline_markup(constants.DEAL_TYPES),
    )
    context.user_data.clear()
    return utils.State.DEALS


@utils.inject_db_session_and_client
async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    sell_count = await session.scalar(
        select(func.count(Deal.id)).filter(
            Deal.client_id == client.id, Deal.deal_type == "sell"
        )
    )
    if sell_count == 0:
        await query.edit_message_text(
            messages.stats_is_empty[client.lang],
            reply_markup=utils.get_main_menu_inline_markup(),
        )
        return utils.State.MAIN_MENU
    else:
        buttons = ("Newest", "%", "Value")
        await query.edit_message_text(
            messages.sort_stats_key_message[client.lang],
            reply_markup=utils.get_inline_markup(buttons=buttons),
        )
    return utils.State.STATS


@utils.inject_db_session_and_client
async def tracking(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    item_count = await session.scalar(
        select(func.count(distinct(Item.name))).filter(
            Item.client_id == client.id,
            Deal.item_id == Item.id,
            Deal.closed.is_(False),
            Deal.deal_type == "buy",
        )
    )
    if item_count == 0:
        await query.edit_message_text(
            messages.tracking_is_empty[client.lang],
            reply_markup=utils.get_main_menu_inline_markup(),
        )
        return utils.State.MAIN_MENU
    else:
        buttons = ("%", "Value")
        await query.edit_message_text(
            messages.sort_key_message[client.lang],
            reply_markup=utils.get_inline_markup(buttons=buttons),
        )
    return utils.State.TRACKING


@utils.inject_db_session_and_client
async def notifications(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    await query.edit_message_text(
        messages.notify_type_choose[client.lang],
        reply_markup=utils.get_inline_markup(constants.NOTIFY_TYPES),
    )
    context.user_data.clear()
    return utils.State.NOTIFICATIONS
