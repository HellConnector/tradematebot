import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from bot.db import Deal, Item, Price, get_async_session
from mini_app_api.data_loader import (
    ALL_SEARCH_ITEMS,
    get_item_with_deals_by_name,
    get_portfolio_data,
)
from mini_app_api.dependencies import (
    ClientDep,
    get_client,
)
from mini_app_api.models import (
    DealCreate,
    PortfolioItem,
    PortfolioSummary,
)

router = APIRouter(
    prefix="/api/portfolio",
    dependencies=[Depends(get_client)],
)


@router.get(path="/")
async def portfolio(client: ClientDep) -> PortfolioSummary:
    async with get_async_session() as session:
        items = await get_portfolio_data(
            client_id=client.id, currency=client.currency, session=session
        )
    if not items:
        raise HTTPException(status_code=404, detail="Portfolio is empty")
    spent_value = sum(item.count * item.buy_price for item in items)
    current_value = sum(item.count * item.current_price for item in items)
    profit = current_value * 0.87 - spent_value
    return PortfolioSummary(
        items=items,
        spent_value=spent_value,
        current_value=current_value,
        profit=profit,
    )


@router.get(path="/items/{item_name}/details/")
async def get_client_item_deals_by_name(
    client: ClientDep, item_name: str
) -> PortfolioItem:
    if "\x00" in item_name:
        raise HTTPException(status_code=400)
    result = await get_item_with_deals_by_name(client, item_name)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Item [{item_name}] not found"
        )
    return result


@router.post(path="/create-deal/")
async def create_deal(client: ClientDep, deal: DealCreate) -> int:
    if deal.item_name not in ALL_SEARCH_ITEMS:
        raise HTTPException(
            status_code=404, detail=f"Item [{deal.item_name}] not found"
        )
    async with get_async_session() as session:
        item = await session.scalar(
            client.items.select()
            .where(Item.name == deal.item_name)
            .options(selectinload(Item.deals))
        )
        if deal.deal_type == "Sell":
            if (
                item is None
                or item.count == 0
                or item.count < deal.deal_volume
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "You can't sell an item that you don't have so "
                        "you need to buy it first. "
                        "Or maybe you are trying to sell more items than "
                        "you have in portfolio.",
                    ),
                )
        if item is None:
            item = Item(
                client_id=client.id,
                name=deal.item_name,
                count=deal.deal_volume,
            )
            session.add(item)
            await session.flush()
            db_price = await session.scalar(
                select(Price.id).filter(
                    Price.name == deal.item_name,
                    Price.currency == client.currency,
                )
            )
            if db_price is None:
                session.add(
                    Price(
                        name=deal.item_name,
                        currency=client.currency,
                        price=0.0,
                        updated=dt.datetime.now(),
                    )
                )
                await session.flush()
        else:
            item_count = (
                deal.deal_volume
                if deal.deal_type == "Buy"
                else -deal.deal_volume
            )
            item.count += item_count
        closed = True if item.count == 0 else False
        item_id = item.id
        db_deal = Deal(
            client_id=client.id,
            item_id=item_id,
            price=deal.deal_price,
            deal_type=deal.deal_type.lower(),
            volume=deal.deal_volume,
            date=dt.datetime.now(),
            deal_currency=client.currency,
            closed=closed,
        )
        session.add(db_deal)
        # If the deal is closed, then we close all open deals on this item
        if closed:
            upd_stmt = (
                update(Deal)
                .where(Deal.item_id == item_id)
                .where(Deal.client_id == client.id)
                .where(Deal.closed.is_(False))
                .values(closed=closed)
            )
            await session.execute(upd_stmt)
    return 200
