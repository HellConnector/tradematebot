from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update, User
from telegram.ext import ContextTypes

from bot import constants, messages, utils
from bot.db import Client


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
