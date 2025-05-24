import hashlib
import hmac
import json
from typing import Literal, Annotated
from urllib.parse import unquote

from pydantic import (
    BaseModel,
    model_validator,
    PrivateAttr,
    ConfigDict,
    AfterValidator,
    field_validator,
)
from pydantic.alias_generators import to_camel
from typing_extensions import Self

from bot import settings


def round_to_two_decimal(v: float) -> float:
    return round(v, 2)


Float2 = Annotated[float, AfterValidator(round_to_two_decimal)]
CurrencyType = Literal["$", "€", "₽", "₴"]


# https://core.telegram.org/bots/webapps#webappuser
class WebAppUser(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    is_premium: bool | None = None
    added_to_attachment_menu: bool | None = None
    allows_write_to_pm: bool | None = None
    photo_url: str | None = None

    _raw_data: str = PrivateAttr(default=None)

    @property
    def raw_data(self) -> str:
        return self._raw_data

    def __init__(
        self,
        raw_data: str,
    ):
        super().__init__(**json.loads(raw_data))
        self._raw_data = raw_data


# https://core.telegram.org/bots/webapps#webappinitdata
class WebAppInitData(BaseModel):
    auth_date: int
    hash: str
    signature: str
    can_send_after: int | None = None
    chat_instance: str | None = None
    chat_type: str | None = None
    start_param: str | None = None
    query_id: str | None = None
    user: WebAppUser | None = None

    def __init__(self, raw_data: str):
        init_data_dict = {
            key: value
            for key, value in map(
                lambda x: x.split("="), unquote(raw_data).split("&")
            )
        }
        init_data_dict.update({"user": WebAppUser(init_data_dict.get("user"))})
        super().__init__(**init_data_dict)

    @property
    def sorted_fields(self) -> list[str]:
        return sorted(filter(lambda x: x != "hash", self.model_fields.keys()))

    # https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    @model_validator(mode="after")
    def validate_init_data(self) -> Self:
        data_check_string = "\n".join(
            map(
                lambda x: f"{x}={getattr(self, x) if x != 'user' else self.user.raw_data}",
                filter(
                    lambda x: getattr(self, x) is not None, self.sorted_fields
                ),
            )
        )

        secret_key = hmac.new(
            "WebAppData".encode(), settings.BOT_TOKEN.encode(), hashlib.sha256
        ).digest()

        expected_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not expected_hash == self.hash:
            raise ValueError(
                f"actual hash: {self.hash} != expected_hash: {expected_hash}"
            )
        return self


class SearchItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    image_url: str


class ItemDeal(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    deal_type: Literal["Buy", "Sell"]
    price: Float2
    volume: int
    currency: CurrencyType
    date: str


class PortfolioItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    image_url: str
    delta_days: int
    count: int
    currency: CurrencyType
    buy_price: Float2
    current_price: Float2
    income_percentage: Float2
    income_amount: Float2
    deals: list[ItemDeal] | None = None


class PortfolioSummary(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    profit: Float2
    spent_value: Float2
    current_value: Float2
    items: list[PortfolioItem]


class StatsItem(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    item_name: str
    image_url: str
    hold_days: int
    left_count: int
    buy_count: int
    avg_buy_price: Float2
    spent_by_item: Float2
    sell_count: int
    avg_sell_price: Float2
    earned_by_item: Float2
    income_abs: Float2
    income_prc: Float2


class StatsSummary(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    items: list[StatsItem]
    total_spent: Float2
    total_earned: Float2
    total_profit: Float2
    currency: CurrencyType


class DealCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    item_name: str
    deal_type: Literal["Buy", "Sell"]
    deal_price: Float2
    deal_volume: int

    @field_validator("item_name")
    def validate_item_name(cls, value):
        if len(value) > 100:
            raise ValueError("Invalid item_name")
        return value

    @field_validator("deal_price")
    def validate_price(cls, value):
        if value < 0.01:
            raise ValueError("Price cannot be negative or too small")
        if value > 1_000_000:
            raise ValueError("Price cannot be greater than 1000000")
        return value

    @field_validator("deal_volume")
    def validate_volume(cls, value):
        if value <= 0:
            raise ValueError("Volume cannot be negative or zero")
        if value > 1000:
            raise ValueError("Volume cannot be greater than 1000")
        return value
