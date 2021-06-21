import gc

from sqlalchemy import distinct
from telegram import Update
from telegram.ext import CallbackContext

import bot.messages as messages
import bot.picture_generator as pg
import bot.utils as bu
from bot.db import get_session
from bot.models import Client, Deal


def get_tracking_table(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    query = update.callback_query
    with get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).first()

        currency_list = s.query(distinct(Deal.deal_currency)).filter(
            Deal.client_id == client.id, Deal.closed.is_(False), Deal.deal_type == 'buy').all()

        query.edit_message_text(messages.tracking_generation_message[client.lang])

        for currency in currency_list:
            pictures = pg.get_tracking_pic(user.id, *currency, query.data, s)
            for picture in pictures:
                user.send_document(document=picture)

    gc.collect()
    return bu.MAIN_MENU
