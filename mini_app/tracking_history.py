from enum import Enum
from typing import Sequence, Iterator

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import (
    get_tracking_records_for_user,
    TrackingRecord,
    Client,
)


class DateRange(Enum):
    day = 1
    week = 7
    month = 30

    @classmethod
    def names(cls) -> Iterator[str]:
        return map(lambda x: x.name, iter(cls))


def split_tracking_records(
    tracking_records: Sequence[TrackingRecord],
) -> dict[str, list[str | float]]:
    result = {
        "labels": [],
        "values": [],
        "incomes": [],
    }

    for record in tracking_records:
        result["labels"].append(record.measure_time.strftime("%d/%m/%Y %H:%M"))
        result["values"].append(round(record.value, 2))
        result["incomes"].append(round(record.income, 2))

    return result


async def get_splitted_tracking_records(
    client: Client, span: DateRange, session: AsyncSession
) -> dict[str, list[float]]:
    tracking_records = await get_tracking_records_for_user(client, span.value, session)
    return split_tracking_records(tracking_records)
