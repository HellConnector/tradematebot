import hashlib
import hmac
import json
import os
from typing import Annotated
from urllib.parse import unquote

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select

from bot.db import get_async_session, Client, get_stats_data, get_tracking_data

load_dotenv()

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")

templates = Jinja2Templates(directory="mini-app/templates")

CURRENCY = {"USD": "$", "EUR": "€", "RUB": "₽", "UAH": "₴"}


class RawInitData(BaseModel):
    init_data: str

    @property
    def user_id(self) -> int | None:
        unquoted = unquote(self.init_data)
        [user] = {
            key: value
            for key, value in map(lambda x: x.split("="), unquoted.split("&"))
            if key == "user"
        }.values()
        user = json.loads(user)

        return user.get("id")


def is_valid_raw_init_data(authorization: Annotated[RawInitData, Header()]):
    string_init_data = unquote(authorization.init_data)

    if not (
        "auth_date=" in string_init_data
        and "query_id=" in string_init_data
        and "user=" in string_init_data
        and "hash=" in string_init_data
    ):
        return False

    pairs = {
        key: value
        for key, value in map(lambda x: x.split("="), string_init_data.split("&"))
    }
    # Alphabetically sorted by keys
    data_check_string = "\n".join(
        (
            f"auth_date={pairs['auth_date']}",
            f"query_id={pairs['query_id']}",
            f"user={pairs['user']}",
        )
    )
    secret_key = hmac.new(
        "WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return expected_hash == pairs["hash"]


@app.get(
    "/stats/load/",
    response_class=HTMLResponse,
)
async def load_stats(
    request: Request,
    authorization: Annotated[str, Header()],
    sort: str | None = None,
) -> HTMLResponse:
    if not is_valid_raw_init_data(
        raw_init_data := RawInitData(init_data=authorization)
    ):
        print("invalid init_data ", authorization)
        raise HTTPException(status_code=400, detail="Invalid raw_init_data")

    match sort:
        case "newest":
            sort_key = "Newest"
        case "value":
            sort_key = "Value"
        case _:
            sort_key = "Percent"

    user_id = raw_init_data.user_id
    async with get_async_session() as session:
        client = await session.scalar(select(Client).where(Client.chat_id == user_id))
        stats_data = await get_stats_data(
            client_id=client.id,
            currency=client.currency,
            sort_key=sort_key,
            session=session,
        )
    items = [
        {
            "name": data[0],
            "hold_days": int(data[1]),
            "left": int(data[2]),
            "buy_count": int(data[3]),
            "buy_price": round(data[4], 2),
            "spent": round(data[5], 2),
            "sell_count": int(data[6]),
            "sell_price": round(data[7], 2),
            "earned": round(data[8], 2),
            "income_value": round(data[9], 2),
            "income_percentage": round(data[10], 2),
        }
        for data in stats_data
    ]
    spent = round(sum(item["spent"] for item in items), 2)
    earned = round(sum(item["earned"] for item in items), 2)
    income = round(earned - spent, 2)
    template = templates.TemplateResponse(
        "stats-data.html",
        {
            "request": request,
            "items": items,
            "spent": spent,
            "earned": earned,
            "income": income,
            "currency": CURRENCY[client.currency],
        },
    )
    return template


@app.get("/tracking/load/", response_class=HTMLResponse)
async def load_tracking(
    request: Request, authorization: Annotated[str, Header()], sort: str | None = None
) -> HTMLResponse:
    if not is_valid_raw_init_data(
        raw_init_data := RawInitData(init_data=authorization)
    ):
        raise HTTPException(status_code=400, detail="Empty raw_init_data")

    user_id = raw_init_data.user_id
    async with get_async_session() as session:
        client = await session.scalar(select(Client).where(Client.chat_id == user_id))
        tracking_data = await get_tracking_data(
            chat_id=user_id, currency=client.currency, session=session
        )
        # Sort deals
        # index=6 - income(%), index=7 - income($)
        tracking_data.sort(
            key=lambda x: x[7 if sort and sort == "value" else 6], reverse=True
        )

    items = [
        {
            "hold_days": int(data[0]),
            "name": data[1],
            "count": int(data[2]),
            "buy_price": round(data[4], 2),
            "current_price": round(data[5], 2),
            "income_percent": round(data[6], 2),
            "income_value": round(data[7], 2),
        }
        for data in tracking_data
    ]
    spent = round(sum(item["count"] * item["buy_price"] for item in items), 2)
    current_value = round(
        sum(item["count"] * item["current_price"] for item in items), 2
    )
    profit = round(current_value * 0.87 - spent, 2)

    template = templates.TemplateResponse(
        "tracking-data.html",
        context={
            "request": request,
            "items": items,
            "spent": spent,
            "current_value": current_value,
            "profit": profit,
            "currency": CURRENCY[client.currency],
        },
    )
    return template


@app.get("/stats/", response_class=HTMLResponse)
async def stats(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("stats.html", context={"request": request})


@app.get("/tracking/", response_class=HTMLResponse)
async def tracking(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("tracking.html", context={"request": request})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", context={"request": request})


def run():
    uvicorn.run("mini-app.main:app", port=5000, reload=True)


if __name__ == "__main__":
    run()
