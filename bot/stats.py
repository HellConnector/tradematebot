import gc

from sqlalchemy import distinct, select
from telegram import Update
from telegram.ext import ContextTypes

import messages as messages
import picture_generator as pg
import utils
from db import Client, Deal, get_async_session


async def get_items_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await utils.get_tg_user(update)
    query = update.callback_query
    async with get_async_session() as s:
        client = await s.scalar(select(Client).where(Client.chat_id == user.id))

        currency_list = await s.scalars(
            select(distinct(Deal.deal_currency)).filter(
                Deal.client_id == client.id,
                Deal.deal_type == "sell",
            )
        )

        await query.edit_message_text(messages.stats_generation_message[client.lang])

        for currency in currency_list:
            pictures = await pg.get_stats_pic(client.id, currency, query.data, s)
            for picture in pictures:
                await user.send_document(document=picture)

    gc.collect()
    return utils.State.MAIN_MENU
