from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func

from bot.db import get_async_session, Deal
from mini_app_api.data_loader import CURRENCY_MAP
from mini_app_api.dependencies import (
    InitDataDep,
    ClientDep,
    get_web_app_init_data,
    get_client,
)

router = APIRouter(
    prefix="/api/profile",
    dependencies=[Depends(get_web_app_init_data), Depends(get_client)],
)


@router.get(path="/")
async def profile(init_data: InitDataDep, client: ClientDep) -> dict:
    user = init_data.user
    async with get_async_session() as session:
        subquery = (
            select(Deal.item_id)
            .where(Deal.client_id == client.id, Deal.closed == False)
            .group_by(Deal.item_id)
        )
        query = select(func.count()).select_from(subquery.subquery())
        open_deals_items_count = await session.scalar(query)

    user_dict = user.model_dump(by_alias=True)
    user_dict["openDealsItemsCount"] = open_deals_items_count

    return user_dict


@router.get(path="/settings/")
async def get_settings(client: ClientDep) -> dict:
    if client:
        return {"lang": client.lang, "currency": CURRENCY_MAP[client.currency]}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
