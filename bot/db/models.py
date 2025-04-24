import datetime as dt
from typing import List
from typing import Self

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    BigInteger,
)
from sqlalchemy.orm import relationship, DeclarativeBase, mapped_column

from bot import constants

CSGO_ID = 730
CSGO = "CSGO"
DEFAULT_ITEM_LIMIT = 96


# TODO Remove fields that don't used in search


class Base(DeclarativeBase):
    pass


class Client(Base):
    """
    ORM-model for clients.

    Attributes:
        name (str): telegram username
        chat_id (int): telegram chat_id
        currency (str): client currency
        item_limit (int): tracking item limit
        lang (str): client language
    """

    __tablename__ = "clients"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    name = mapped_column(String, nullable=False, unique=False, index=True)
    chat_id = mapped_column(
        BigInteger, nullable=False, unique=True, primary_key=True, index=True
    )
    currency = mapped_column(String, default="USD", index=True)
    item_limit = mapped_column(Integer, default=DEFAULT_ITEM_LIMIT)
    lang = mapped_column(String, default="EN")

    items = relationship("Item", lazy="write_only")
    tracking_records = relationship("TrackingRecord", lazy="write_only")

    def __init__(
        self,
        name,
        chat_id,
        currency="USD",
        item_limit=DEFAULT_ITEM_LIMIT,
        lang="EN",
    ):
        self.name = name
        self.chat_id = chat_id
        self.currency = currency
        self.item_limit = item_limit
        self.lang = lang


class Item(Base):
    """
    ORM-model for items.

    Attributes:
        client_id (int): client id (foreign key)
        name (str): item full name
        app_id (int): steam store app id
        app_name (str): steam store app name
        count (int): current count in inventory
        take_profit (float): take profit threshold for notification
        stop_loss (float): stop loss threshold for notification
        profit_notify (bool): take profit notification flag
        loss_notify (bool): stop loss notification flag
        updated (DateTime): last update date for item count
    """

    __tablename__ = "items"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, unique=True
    )
    client_id = mapped_column(
        Integer, ForeignKey(Client.id), nullable=False, index=True
    )
    name = mapped_column(String, nullable=False, primary_key=True, index=True)
    app_id = mapped_column(Integer, nullable=False, default=CSGO_ID)
    app_name = mapped_column(String, nullable=False, default=CSGO)
    count = mapped_column(Integer, nullable=False, default=0)
    take_profit = mapped_column(Float(precision=2), default=None)
    stop_loss = mapped_column(Float(precision=2), default=None)
    profit_notify = mapped_column(Boolean, default=False)
    loss_notify = mapped_column(Boolean, default=False)
    updated = mapped_column(DateTime, onupdate=dt.datetime.now)

    deals = relationship("Deal", lazy="selectin")

    def __init__(
        self,
        client_id,
        name,
        app_id=CSGO_ID,
        app_name=CSGO,
        count=0,
        take_profit=None,
        stop_loss=None,
        profit_notify=False,
        loss_notify=False,
    ):
        self.client_id = client_id
        self.name = name
        self.app_id = app_id
        self.app_name = app_name
        self.count = count
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.profit_notify = profit_notify
        self.loss_notify = loss_notify
        self.updated = dt.datetime.now()


class Deal(Base):
    """
    ORM-model for deal.

    Attributes:
        client_id (int): client id (foreign key)
        item_id (int): item id (foreign key)
        deal_type (str): deal type ('buy' or 'sell')
        price (float): deal price
        volume (int): deal volume (items count with item_id)
        deal_currency (str): deal currency
        date (DateTime): deal date (record to database date)
        closed (bool): deal closed flag
    """

    __tablename__ = "deals"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, unique=True
    )
    client_id = mapped_column(
        Integer, ForeignKey(Client.id), nullable=False, index=True
    )
    item_id = mapped_column(
        Integer, ForeignKey(Item.id), nullable=False, index=True
    )
    deal_type = mapped_column(String, nullable=False, index=True)
    price = mapped_column(Float(precision=2), nullable=False)
    volume = mapped_column(Integer, nullable=False)
    deal_currency = mapped_column(String, nullable=False, index=True)
    date = mapped_column(DateTime, nullable=False)
    closed = mapped_column(Boolean, default=False)

    def __init__(
        self,
        client_id,
        item_id,
        deal_type,
        price,
        volume,
        deal_currency,
        date,
        closed=False,
    ):
        self.client_id = client_id
        self.item_id = item_id
        self.deal_type = deal_type
        self.price = price
        self.volume = volume
        self.deal_currency = deal_currency
        self.date = date
        self.closed = closed


class Skin(Base):
    __tablename__ = "skins"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    skin_type = mapped_column(String, nullable=False, index=True)
    collection = mapped_column(String, index=True)
    name = mapped_column(String, nullable=False, index=True)
    skin = mapped_column(String, index=True)
    full_name = mapped_column(String, nullable=False, index=True)
    fn = mapped_column(Boolean, default=False)
    mw = mapped_column(Boolean, default=False)
    ft = mapped_column(Boolean, default=False)
    ww = mapped_column(Boolean, default=False)
    bs = mapped_column(Boolean, default=False)
    st = mapped_column(Boolean, default=False)
    sv = mapped_column(Boolean, default=False)

    quality = dict(zip(constants.WEAPON_QUALITY.keys(), [fn, mw, ft, ww, bs]))

    def __init__(
        self,
        skin_type,
        collection,
        name,
        skin,
        full_name,
        fn=False,
        mw=False,
        ft=False,
        ww=False,
        bs=False,
        st=False,
        sv=False,
    ):
        self.skin_type = skin_type
        self.collection = collection
        self.name = name
        self.skin = skin
        self.full_name = full_name
        self.fn = fn
        self.mw = mw
        self.ft = ft
        self.ww = ww
        self.bs = bs
        self.st = st
        self.sv = sv

    def get_names(self) -> List[str]:
        """A method that returns all possible variations of a name by quality.

        Returns:
            List[str]: list with item names.
        """
        q_cols = dict(
            zip(
                self.quality.keys(),
                [self.fn, self.mw, self.ft, self.ww, self.bs],
            )
        )
        names = [
            f"{self.full_name} ({constants.WEAPON_QUALITY[k]})"
            for k in q_cols
            if q_cols[k] is True
        ]
        if self.skin is None:  # statement for Vanilla knives
            names.append(self.full_name)
        return names

    @classmethod
    def from_dict(cls, skin_dict) -> Self:
        return cls(**skin_dict)


class Container(Base):
    __tablename__ = "containers"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    container_type = mapped_column(String, nullable=False)
    name = mapped_column(String, index=True)

    def __init__(self, container_type, name):
        self.container_type = container_type
        self.name = name


class Agent(Base):
    __tablename__ = "agents"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    side = mapped_column(String, nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True, unique=True)

    def __init__(self, side, name):
        self.side = side
        self.name = name


class Sticker(Base):
    __tablename__ = "stickers"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    sticker_type = mapped_column(String, nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)  # TODO remove
    full_name = mapped_column(String, nullable=False, index=True)
    collection = mapped_column(String)  # TODO remove
    tournament = mapped_column(
        String, nullable=True, default=None
    )  # TODO remove

    def __init__(
        self, sticker_type, name, full_name, collection, tournament=None
    ):
        self.sticker_type = sticker_type
        self.name = name
        self.full_name = full_name
        self.collection = collection
        self.tournament = tournament

    @classmethod
    def from_hashname(cls, sticker_type: str, hashname: str) -> Self:
        return cls(sticker_type, hashname, hashname, None)


class Tool(Base):
    __tablename__ = "tools"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    name = mapped_column(String, nullable=False, index=True, unique=True)

    def __init__(self, name):
        self.name = name


class Price(Base):
    __tablename__ = "prices"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    name = mapped_column(
        String, nullable=False, index=True, unique=False, primary_key=True
    )
    price = mapped_column(Float(precision=2), default=0.0)
    currency = mapped_column(
        String, default="USD", index=True, primary_key=True
    )
    updated = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "currency", name="_name_currency_uc"),
    )

    def __init__(self, name, price, updated, currency="USD"):
        self.name = name
        self.price = price
        self.currency = currency
        self.updated = updated


class PriceLimit(Base):
    __tablename__ = "price_limits"
    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True, unique=True
    )
    currency = mapped_column(String, index=True, unique=True)
    value = mapped_column(Float(precision=2), default=0.0)
    updated = mapped_column(DateTime, nullable=False)

    def __init__(self, currency, value, updated):
        self.currency = currency
        self.value = value
        self.updated = updated


class TrackingRecord(Base):
    __tablename__ = "tracking_records"

    id = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    client_id = mapped_column(
        Integer, ForeignKey(Client.id), nullable=False, index=True
    )
    currency = mapped_column(String, index=True, nullable=False)
    value = mapped_column(Float(precision=2), default=0.0)
    income = mapped_column(Float(precision=2), default=0.0)
    measure_time = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class SearchItem(Base):
    __tablename__ = "search_items"

    name = mapped_column(String, primary_key=True)
    image_url = mapped_column(String, nullable=False)
