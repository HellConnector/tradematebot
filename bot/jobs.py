from sqlalchemy import select
from telegram import ReplyKeyboardRemove
from telegram.ext import ContextTypes

from bot import utils, messages
from bot.db import get_async_session, Client, Item, Price
from bot.db.data_helper import get_tracking_records
from bot.db.models import TrackingRecord, PriceLimit
from bot.logger import log


async def update_price_limits(context: ContextTypes.DEFAULT_TYPE):
    limits = await utils.update_price_limits()
    if not limits:
        async with get_async_session() as session:
            limits = {
                "price_limits": {
                    limit.currency: round(limit.value, 2)
                    for limit in (
                        await session.scalars(select(PriceLimit))
                    ).all()
                }
            }
    store_price_limits_in_bot_data(context, limits)


def store_price_limits_in_bot_data(context: ContextTypes.DEFAULT_TYPE, limits):
    context.bot_data.update(limits)


async def send_notifications(context: ContextTypes.DEFAULT_TYPE):
    async with get_async_session() as session:
        take_profit_data = (
            await session.execute(
                select(
                    Client.chat_id,
                    Client.currency,
                    Item.name,
                    Item.take_profit,
                    Price.price,
                ).where(
                    Client.id == Item.client_id,
                    Item.name == Price.name,
                    Price.price > Item.take_profit,
                    Client.currency == Price.currency,
                    Item.profit_notify.is_(True),
                )
            )
        ).all()

        for chat_id in set(j[0] for j in take_profit_data):
            client = await session.scalar(
                select(Client).where(Client.chat_id == chat_id)
            )
            items_data = [
                i[1:]
                for i in filter(lambda x: x[0] == chat_id, take_profit_data)
            ]
            items_str = "\n".join(
                f"{i + 1}) `{utils.get_short_name(d[1])}`:\n`{d[2]} {d[0]}` ⇒ "
                f"`{round(d[3], 2)} {d[0]}`"
                for i, d in enumerate(items_data)
            )
            message = f"{messages.notify_take_profit_reached[client.lang]}{items_str}"

            # Sending message
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=ReplyKeyboardRemove(),
                )
            except Exception:
                log.info(f"Failed to send message to chat [{chat_id}]")

            # Turning notification flag to False
            client_items = (
                await session.scalars(
                    client.items.select().where(
                        Item.name.in_(x[1] for x in items_data)
                    )
                )
            ).all()
            for item in client_items:
                item.profit_notify = False


async def update_tracking_records(context: ContextTypes.DEFAULT_TYPE):
    async with get_async_session() as session:
        tracking_records = await get_tracking_records(session)
        for client_id, currency, value, income in tracking_records:
            session.add(
                TrackingRecord(
                    client_id=client_id,
                    currency=currency,
                    value=value,
                    income=income,
                )
            )
