from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.db import Client, Deal, Item, Price, SearchItem, get_async_session
from bot.db.data_helper import get_stats_data
from mini_app_api.models import ItemDeal, PortfolioItem, StatsItem

ALL_SEARCH_ITEMS = {}

CURRENCY_MAP = {"USD": "$", "EUR": "€", "RUB": "₽", "UAH": "₴"}


async def get_existing_search_items() -> dict[str, str]:
    async with get_async_session() as session:
        existing_items = await session.scalars(select(SearchItem))
    return {item.name: item.image_url for item in existing_items}


async def get_portfolio_data(
    client_id: int, currency: str, session: AsyncSession
) -> list[PortfolioItem]:
    query = (
        select(
            func.min(Deal.date),
            Item.name,
            SearchItem.image_url,
            Item.count,
            func.sum(Deal.price * Deal.volume)
            / func.sum(Deal.volume).label("avg_price"),
            Price.price,
            Deal.deal_currency,
        )
        .join(Item, Deal.item_id == Item.id)
        .join(Price, Item.name == Price.name)
        .join(SearchItem, Item.name == SearchItem.name)
        .where(
            Deal.client_id == client_id,
            Deal.deal_type == "buy",
            Deal.closed.is_(False),
            Item.count > 0,
            Deal.deal_currency == Price.currency,
            Deal.deal_currency == currency,
            Item.client_id == client_id,
        )
        .group_by(
            Deal.item_id,
            Item.name,
            SearchItem.image_url,
            Price.price,
            Item.count,
            Deal.deal_currency,
        )
    )

    client_deals = await session.execute(query)

    deals = []

    for d_date, name, image_url, count, buy, price, currency in client_deals:
        # hold days
        deal_date = datetime.date(d_date)
        current_date = datetime.strptime(
            date.today().isoformat(), "%Y-%m-%d"
        ).date()
        delta_days = current_date - deal_date

        # income in percent
        price_with_tax = price * 0.87
        try:
            income_percentage = (price_with_tax - buy) / buy * 100
        except ZeroDivisionError:
            income_percentage = price_with_tax

        # income in currency
        income_amount = (price_with_tax - buy) * count

        deals.append(
            PortfolioItem(
                name=name,
                image_url=image_url,
                delta_days=delta_days.days,
                count=count,
                currency=CURRENCY_MAP[currency],
                buy_price=buy,
                current_price=price,
                income_percentage=income_percentage,
                income_amount=income_amount,
            )
        )
    if deals:
        deals.sort(key=lambda x: x.income_percentage, reverse=True)

    return deals


async def get_stats_data_for_client(
    client_id: int, currency: str, session: AsyncSession
) -> list[StatsItem]:
    stats_data = await get_stats_data(client_id, currency, session)

    results = [
        StatsItem(
            item_name=item.item_name,
            image_url=item.image_url,
            hold_days=item.hold_days,
            left_count=item.left_count,
            buy_count=item.buy_count,
            avg_buy_price=item.avg_buy_price,
            spent_by_item=item.spent_by_item,
            sell_count=item.sell_count,
            avg_sell_price=item.avg_sell_price,
            earned_by_item=item.earned_by_item,
            income_abs=item.income_abs,
            income_prc=item.income_prc,
        )
        for item in stats_data
    ]

    if results:
        results.sort(key=lambda x: x.income_prc, reverse=True)

    return results


async def get_item_with_deals_by_name(
    client: Client, item_name: str
) -> PortfolioItem | None:
    query = (
        select(Item, Price.price)
        .join(Price, Item.name == Price.name)
        .where(
            Item.client_id == client.id,
            Item.name == item_name,
            Price.currency == client.currency,
        )
        .options(selectinload(Item.deals))
    )
    async with get_async_session() as session:
        query_result = (await session.execute(query)).one_or_none()
        if not query_result:
            return None
        item, current_price = query_result

    buy_price = sum(
        map(
            lambda d: d.price * d.volume,
            filter(lambda d: d.deal_type == "buy", item.deals),
        )
    ) / sum(
        map(
            lambda d: d.volume,
            filter(lambda d: d.deal_type == "buy", item.deals),
        )
    )

    income_percentage = (
        current_price * 0.87
        if buy_price == 0
        else (current_price * 0.87 - buy_price) / buy_price * 100
    )

    current_date = datetime.strptime(
        date.today().isoformat(), "%Y-%m-%d"
    ).date()

    min_buy_deal_date = min(
        datetime.date(d.date) for d in item.deals if d.deal_type == "buy"
    )
    max_sell_deal_date = max(
        (datetime.date(d.date) for d in item.deals if d.deal_type == "sell"),
        default=current_date,
    )

    delta_days = (
        (current_date - min_buy_deal_date).days
        if item.count > 0
        else (max_sell_deal_date - min_buy_deal_date).days
    )

    portfolio_item = PortfolioItem(
        name=item.name,
        currency=CURRENCY_MAP[client.currency],
        image_url=ALL_SEARCH_ITEMS[item.name],
        deals=[
            ItemDeal(
                deal_type=deal.deal_type.capitalize(),
                price=deal.price,
                volume=deal.volume,
                currency=CURRENCY_MAP[deal.deal_currency],
                date=deal.date.strftime("%d.%m.%Y %H:%M"),
            )
            for deal in item.deals
        ],
        buy_price=buy_price,
        current_price=current_price,
        income_percentage=income_percentage,
        income_amount=(current_price * 0.87 - buy_price) * item.count,
        delta_days=delta_days,
        count=item.count,
    )

    return portfolio_item
