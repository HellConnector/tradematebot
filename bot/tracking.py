import gc

from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update, User
from telegram.ext import ContextTypes

import messages as messages
import picture_generator as pg
import utils
from db import Client, Deal


@utils.inject_db_session_and_client
async def get_tracking_table(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query

    currency_list = await session.scalars(
        select(distinct(Deal.deal_currency)).filter(
            Deal.client_id == client.id,
            Deal.closed.is_(False),
            Deal.deal_type == "buy",
        )
    )

    await query.edit_message_text(messages.tracking_generation_message[client.lang])

    for currency in currency_list:
        pictures = await pg.get_tracking_pic(user.id, currency, query.data, session)
        for picture in pictures:
            await user.send_document(document=picture)

    gc.collect()
    return utils.State.MAIN_MENU
