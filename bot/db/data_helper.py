from datetime import datetime, timedelta
from typing import Sequence

from sqlalchemy import select, func, case, Subquery, Numeric, Float
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Deal, Item, Client, Price, TrackingRecord, SearchItem


async def get_stats_data(
    client_id: int, currency: str, session: AsyncSession
) -> list:
    income_abs = "income_abs"
    income_prc = "income_prc"

    ie = (
        select(
            Deal.item_id,
            Item.name.label("item_name"),
            func.max(Deal.date).label("sell_date"),
            func.sum(Deal.volume).label("sell_count"),
            func.sum(Deal.volume * Deal.price).label("earned_by_item"),
            (func.sum(Deal.price * Deal.volume) / func.sum(Deal.volume)).label(
                "avg_sell_price"
            ),
        )
        .where(
            Item.id == Deal.item_id,
            Deal.client_id == client_id,
            Deal.deal_type == "sell",
            Deal.deal_currency == currency,
        )
        .group_by(Deal.item_id, Item.name)
    )

    ie = ie.cte("items_earned")
    ib = (
        select(
            ie.c.item_id,
            func.min(Deal.date).label("buy_date"),
            func.sum(Deal.volume).label("buy_count"),
            func.sum(Deal.volume * Deal.price).label("spent_by_item"),
            (func.sum(Deal.price * Deal.volume) / func.sum(Deal.volume)).label(
                "avg_buy_price"
            ),
        )
        .where(
            ie.c.item_id == Deal.item_id,
            Deal.client_id == client_id,
            Deal.deal_type == "buy",
            Deal.deal_currency == currency,
        )
        .group_by(ie.c.item_id)
    )
    ib = ib.cte("items_buy")
    stats = select(
        ie.c.item_name,
        SearchItem.image_url,
        func.date_part("day", ie.c.sell_date - ib.c.buy_date).label(
            "hold_days"
        ),
        (ib.c.buy_count - ie.c.sell_count).label("left_count"),
        ib.c.buy_count,
        ib.c.avg_buy_price,
        ib.c.spent_by_item,
        ie.c.sell_count,
        ie.c.avg_sell_price,
        ie.c.earned_by_item,
        (ie.c.earned_by_item - ib.c.spent_by_item).label(income_abs),
        (
            (
                ie.c.earned_by_item
                / case(
                    (ib.c.spent_by_item == 0.0, 1),
                    else_=ib.c.spent_by_item,
                )
                - 1
            )
            * 100
        ).label(income_prc),
    ).where(ie.c.item_id == ib.c.item_id, ie.c.item_name == SearchItem.name)

    return (await session.execute(stats)).all()


async def get_tracking_records(
    session: AsyncSession,
) -> list[tuple[int, str, float, float]]:
    sub_query: Subquery = (
        select(
            Client.id.label("client_id"),
            Client.currency,
            (Item.count * Price.price).label("value"),
            (
                0.87 * Item.count * Price.price
                - (
                    Item.count
                    * func.sum(Deal.price * Deal.volume)
                    / func.sum(Deal.volume)
                )
            ).label("income"),
        )
        .where(
            Client.id == Item.client_id,
            Deal.client_id == Client.id,
            Deal.deal_type == "buy",
            Deal.closed.is_(False),
            Deal.item_id == Item.id,
            Item.name == Price.name,
            Item.count > 0,
            Deal.deal_currency == Price.currency,
        )
        .group_by(Client.id, Client.currency, Item.id, Item.name, Price.price)
    ).subquery()

    query = (
        select(
            Client.id,
            Client.currency,
            func.round(func.sum(sub_query.c.value).cast(Numeric), 2)
            .cast(Float)
            .label("value"),
            func.round(func.sum(sub_query.c.income).cast(Numeric), 2)
            .cast(Float)
            .label("income"),
        )
        .where(
            Client.id == sub_query.c.client_id,
        )
        .group_by(Client.id, Client.currency)
        .order_by(Client.id)
    )

    return (await session.execute(query)).all()


async def get_tracking_records_for_user(
    client: Client, span: int, session: AsyncSession
) -> Sequence[TrackingRecord] | None:
    tracking_records = (
        await session.scalars(
            client.tracking_records.select()
            .where(
                TrackingRecord.currency == client.currency,
                TrackingRecord.measure_time
                >= datetime.now() - timedelta(days=span),
            )
            .order_by(TrackingRecord.measure_time.asc())
        )
    ).all()

    return tracking_records
