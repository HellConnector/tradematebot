from fastapi import APIRouter, Depends, HTTPException

from bot.db import get_async_session
from mini_app_api.data_loader import (
    CURRENCY_MAP,
    get_stats_data_for_client,
)
from mini_app_api.dependencies import ClientDep, get_client
from mini_app_api.models import StatsSummary

router = APIRouter(
    prefix="/api/stats",
    dependencies=[Depends(get_client)],
)


@router.get(path="/")
async def get_stats(client: ClientDep) -> StatsSummary:
    async with get_async_session() as session:
        items = await get_stats_data_for_client(
            client_id=client.id, currency=client.currency, session=session
        )

    if not items:
        raise HTTPException(status_code=404, detail="Stats info is not found")

    total_spent = sum(item.spent_by_item for item in items)
    total_earned = sum(item.earned_by_item for item in items)
    total_profit = total_earned - total_spent

    return StatsSummary(
        items=items,
        total_spent=total_spent,
        total_earned=total_earned,
        total_profit=total_profit,
        currency=CURRENCY_MAP[client.currency],
    )
