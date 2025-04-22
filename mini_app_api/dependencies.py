from typing import Annotated

from fastapi import Header, HTTPException, Depends
from sqlalchemy import select

from bot.db import get_async_session, Client
from mini_app_api.models import WebAppInitData


async def get_web_app_init_data(
    authorization: Annotated[str, Header()],
) -> WebAppInitData:
    try:
        init_data = WebAppInitData(authorization)
    except Exception as exception:
        raise HTTPException(
            status_code=401, detail=str(exception)
        ) from exception
    return init_data


InitDataDep = Annotated[WebAppInitData, Depends(get_web_app_init_data)]


async def get_client(init_data: InitDataDep) -> Client:
    if not init_data.user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    async with get_async_session() as session:
        client = await session.scalar(
            select(Client).where(Client.chat_id == init_data.user.id)
        )

        if not client:
            client = Client(
                name=init_data.user.first_name, chat_id=init_data.user.id
            )
            session.add(client)

    return client


ClientDep = Annotated[Client, Depends(get_client)]
