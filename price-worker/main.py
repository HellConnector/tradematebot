import asyncio
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from itertools import cycle, chain
from typing import Self, Iterator

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

from bot.db import get_async_session, Price, Item, Deal

load_dotenv()

MARKET_URL = "https://steamcommunity.com/market/priceoverview/"
PROXIES_URL = os.getenv("PROXIES_URL")
SEGMENT = int(os.getenv("SEGMENT"))
REQUESTS_PER_ITEM = 10


logger = logging.getLogger("price-worker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class Currency(Enum):
    USD = 1
    EUR = 3
    RUB = 5
    UAH = 18


def timeit(func):
    async def inner(*args, **kwargs):
        start = time.monotonic()
        logger.info("Execution start")
        await func(*args, **kwargs)
        stop = time.monotonic()
        logger.info(f"Execution time = {stop - start:.2f}s")

    return inner


@dataclass
class PriceResponse:
    lowest_price: str | None = None
    median_price: str | None = None
    success: bool | None = None
    volume: str | None = None

    @classmethod
    def from_dict(cls, **kwargs) -> Self:
        return cls(**kwargs)


@dataclass
class MarketItem:
    name: str
    currency: Currency
    price: PriceResponse | None = None

    @property
    def has_price(self) -> bool:
        return (
            self.price.success
            if self.price
            and self.price.success
            and (self.price.median_price or self.price.lowest_price)
            else False
        )

    @property
    def success_no_price(self) -> bool:
        return (
            self.price.success
            if self.price
            and self.price.success
            and (not self.price.median_price and not self.price.lowest_price)
            else False
        )

    @property
    def price_string(self) -> str | None:
        if not self.has_price:
            return
        if self.price.lowest_price:
            return self.price.lowest_price
        else:
            return self.price.median_price

    @property
    def price_float(self) -> float | None:
        if not self.has_price:
            return
        price = self.price_string
        if self.currency == Currency.USD:
            price = price.replace(",", "")
        price = price.replace(",", ".").replace(" ", "")
        price = re.sub(
            r"([$₴€\-\s]|pуб\.)", "", price
        )  # p - English letter in russian currency (WTF Valve #3)
        return float(price)

    def __str__(self):
        if self.has_price:
            return f"[{self.name}] --> [{self.price_string}]"
        else:
            return f"[{self.name}] --> NO PRICE"


class ItemPriceManager:
    def __init__(self, items: Iterator[MarketItem]):
        self.items: dict[str, MarketItem] = {
            self._create_key(item): item for item in items
        }

    @staticmethod
    def _create_key(item: MarketItem) -> str:
        return f"{item.name}-{item.currency.name}"

    @property
    def finished(self) -> bool:
        return all(
            (item.has_price or item.success_no_price) for item in self.items.values()
        )

    @property
    def items_without_price(self) -> Iterator[MarketItem]:
        return (
            item
            for item in self.items.values()
            if not item.has_price or item.success_no_price
        )

    @property
    def success_count(self) -> int:
        return sum(item.has_price for item in self.items.values())

    @property
    def remaining_count(self) -> int:
        return len(self.items.values()) - self.success_count

    def show_progress(self):
        logger.info(
            f"Progress is {100 * self.success_count / len(self.items.values()):.2f}%"
        )

    def update_item(self, item: MarketItem):
        self.items.update({self._create_key(item): item})


def read_items_from_file(file: str) -> set[str]:
    with open(file) as f:
        return set(f.read().splitlines())


async def get_items_from_db() -> Iterator[MarketItem]:
    items_count = 500
    offset = items_count * SEGMENT
    query = (
        select(Item.name.label("item_name"), Deal.deal_currency.label("currency"))
        .where(Item.id == Deal.item_id)
        .group_by(Item.name, Deal.deal_currency)
        .limit(items_count)
        .offset(offset)
    )
    async with get_async_session() as session:
        items = map(
            lambda i: MarketItem(name=i[0], currency=Currency[f"{i[1]}"]),
            (await session.execute(query)).all(),
        )

    return items


def map_item_to_proxy(items: Iterator[MarketItem], proxies: list[str]):
    return zip(items, cycle(proxies))


async def get_http_proxies() -> list[str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(PROXIES_URL)

    return response.content.decode("utf-8").split()


async def get_item_price(
    item: MarketItem, proxy: str, timeout: int
) -> MarketItem | None:
    async with httpx.AsyncClient(
        proxy=f"http://{proxy}",
        timeout=timeout,
        verify=False,
        limits=httpx.Limits(
            max_connections=1, max_keepalive_connections=1, keepalive_expiry=1
        ),
    ) as client:
        try:
            response = await client.get(
                url=MARKET_URL,
                params={
                    "appid": 730,
                    "currency": item.currency.value,
                    "market_hash_name": item.name,
                },
            )
        except Exception:  # Ignore any exceptions here
            return
    if response.status_code == 200:
        item.price = PriceResponse.from_dict(**response.json())
    return item


@timeit
async def main():
    manager = ItemPriceManager(await get_items_from_db())
    async with get_async_session() as session:
        while not manager.finished:
            start = time.monotonic()
            proxies = await get_http_proxies()

            match manager.remaining_count:
                case count if 1 <= count <= 10:
                    timeout = 5
                case count if 11 <= count <= 100:
                    timeout = 10
                case _:
                    timeout = 15

            tasks = (
                get_item_price(*item_proxy, timeout=timeout)
                for item_proxy in map_item_to_proxy(
                    chain(
                        *(manager.items_without_price for _ in range(REQUESTS_PER_ITEM))
                    ),
                    proxies,
                )
            )

            results: list[MarketItem] = list(
                filter(
                    lambda i: i is not None and i.has_price,
                    (await asyncio.gather(*tasks)),
                )
            )

            for item in results:
                db_price = await session.scalar(
                    select(Price).where(
                        Price.name == item.name,
                        Price.currency == item.currency.name,
                    )
                )
                if db_price:
                    db_price.price = item.price_float
                    db_price.updated = datetime.now()
                else:
                    session.add(
                        Price(
                            name=item.name,
                            currency=item.currency.value,
                            updated=datetime.now(),
                            price=item.price_float,
                        )
                    )
                logger.info(item)
            await session.commit()

            stop = time.monotonic()
            logger.info(f"Iteration completed in {stop-start:.2f}s")
            manager.show_progress()
    logger.info(f"----------------------------SUMMARY----------------------------")
    logger.info(f"Has price -> {manager.success_count} items")
    logger.info(f"Doesn't have price -> {manager.remaining_count} items")
    for item in filter(lambda i: i.success_no_price, manager.items.values()):
        logger.info(item)
    logger.info(f"----------------------------SUMMARY----------------------------")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
