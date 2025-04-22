import asyncio
import logging

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

from bot.db import get_async_session, SearchItem

load_dotenv()

logger = logging.getLogger("search-items-worker")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


async def get_json_response(url: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
    return response.json()


async def main() -> None:
    data = await get_json_response(
        "https://api.steamapis.com/image/items/730/"
    )

    async with get_async_session() as session:
        existing_items = await session.scalars(select(SearchItem.name))
        diff = set(
            filter(lambda x: not x.startswith("#"), data.keys())
        ).difference(existing_items)
        if len(diff) > 0:
            session.add_all(
                SearchItem(name=name, image_url=data[name]) for name in diff
            )
            logger.info(f"Found {len(diff)} new items")
            logger.info("\n".join(diff))
        else:
            logger.info("No new items found")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
