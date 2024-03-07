import asyncio
import logging
import os
import time
from dataclasses import dataclass
from itertools import cycle, chain
from typing import Self, Iterator

import httpx
from dotenv import load_dotenv

load_dotenv()

MARKET_URL = "https://steamcommunity.com/market/priceoverview/?appid=730&currency=5&market_hash_name={item_name}"
PROXIES_URL = os.getenv("PROXIES_URL")

logger = logging.getLogger("price-worker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


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
class Item:
    name: str
    price: PriceResponse | None = None

    @property
    def has_price(self) -> bool:
        return self.price.success if self.price and self.price.success else False


class ItemPriceManager:
    MAX_REQUEST_COUNT = 1000

    def __init__(self, items: set[str]):
        self.items: dict[str, Item] = {
            item: Item(name=item, price=None) for item in items
        }

    @property
    def finished(self) -> bool:
        return all(item.has_price for item in self.items.values())

    @property
    def items_without_price(self) -> Iterator[Item]:
        return (item for item in self.items.values() if not item.has_price)

    @property
    def success_count(self) -> int:
        return sum(item.has_price for item in self.items.values())

    @property
    def remaining_count(self) -> int:
        return len(self.items.values()) - self.success_count

    @property
    def scale(self) -> int:
        if self.success_count == len(self.items.values()):
            return 1
        else:
            return self.MAX_REQUEST_COUNT // (
                len(self.items.values()) - self.success_count
            )

    def show_progress(self):
        logger.info(
            f"Progress is {100 * self.success_count / len(self.items.values()):.2f}%"
        )

    def update_item(self, item: Item):
        self.items.update({item.name: item})


def read_items_from_file(file: str) -> set[str]:
    with open(file) as f:
        return set(f.read().splitlines())


def map_item_to_proxy(items: Iterator[Item], proxies: list[str]):
    return list(zip(items, cycle(proxies)))


async def get_http_proxies() -> list[str]:
    async with httpx.AsyncClient() as client:
        response = await client.get(PROXIES_URL)

    return response.content.decode("utf-8").split()


async def get_price(item: Item, proxy: str, timeout: int) -> Item | None:
    async with httpx.AsyncClient(
        proxy=f"http://{proxy}",
        timeout=timeout,
        verify=False,
        limits=httpx.Limits(
            max_connections=1, max_keepalive_connections=1, keepalive_expiry=1
        ),
    ) as client:
        try:
            response = await client.get(url=MARKET_URL.format(item_name=item.name))
        except Exception:
            return
    if response.status_code == 200:
        item.price = PriceResponse.from_dict(**response.json())
    return item


@timeit
async def main():
    items = read_items_from_file("stickers")
    manager = ItemPriceManager(items)

    while not manager.finished:
        start = time.monotonic()
        proxies = await get_http_proxies()

        match manager.remaining_count:
            case count if 1 <= count <= 10:
                timeout = 5
            case count if 11 <= count <= 100:
                timeout = 10
            # case count if 101 <= count <= 250:
            #     timeout = 10
            # case count if 251 <= count <= 500:
            #     timeout = 10
            case _:
                timeout = 15

        tasks = (
            get_price(*item_proxy, timeout=timeout)
            for item_proxy in map_item_to_proxy(
                chain(*(manager.items_without_price for _ in range(10))), proxies
            )
        )

        results = await asyncio.gather(*tasks)
        stop = time.monotonic()
        logger.info(f"Iteration took {stop-start:.2f}s")
        manager.show_progress()
    pass


if __name__ == "__main__":
    asyncio.run(main())
