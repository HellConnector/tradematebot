import datetime as dt
from typing import List

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy.orm import relationship

import bot.names as nm
from bot.db import Base

CSGO_ID = 730
CSGO = 'CSGO'
DEFAULT_ITEM_LIMIT = 96


class Client(Base):
    """
    Класс - отображение сущности пользователя в БД.

    Attributes:
        name (str): Никнейм пользователя
        chat_id (str): ID чата с телеграм-ботом
        currency (str): Валюта
        item_limit (int): Лимит предметов для отслеживания
        lang (str): Язык пользователя
    """
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    name = Column(String, nullable=False, unique=False, index=True)
    chat_id = Column(Integer, nullable=False, unique=True, primary_key=True, index=True)
    currency = Column(String, default='USD', index=True)
    item_limit = Column(Integer, index=True, default=DEFAULT_ITEM_LIMIT)
    lang = Column(String, index=True, default='EN')

    items = relationship('Item', backref='clients', lazy='dynamic')
    deals = relationship('Deal', backref='clients', lazy='dynamic')

    def __init__(self, name, chat_id, currency='USD', item_limit=DEFAULT_ITEM_LIMIT, lang='EN'):
        self.name = name
        self.chat_id = chat_id
        self.currency = currency
        self.item_limit = item_limit
        self.lang = lang

    def __repr__(self):
        return (f"Client('{self.name}', '{self.chat_id}', '{self.lang}', '{self.currency}', "
                f"'{self.item_limit}')")


class Item(Base):
    """
    Класс-отображение сущности предмета в БД.

    Attributes:
        client_id (int): ID пользователя из таблицы users
        name (str): Полное имя предмета
        app_id (int): ID игры в steam
        app_name (str): Сокращённое название игры
        count (int): Текущее количество в инвентаре
        take_profit (float): Порог для уведомления по прибыли
        stop_loss (float): Порог для уведомления по потерям
        profit_notify (bool): Флаг отправки уведомления по прибыли
        loss_notify (bool): Флаг отправки уведомления по потерям
        updated (DateTime): Последняя дата обновления даддых по предметы (количества)
    """
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    client_id = Column(Integer, ForeignKey(Client.id), nullable=False, index=True)
    name = Column(String, nullable=False, primary_key=True, index=True)
    app_id = Column(Integer, nullable=False, default=CSGO_ID, index=True)
    app_name = Column(String, nullable=False, default=CSGO, index=True)
    count = Column(Integer, nullable=False, default=0, index=True)
    take_profit = Column(Float(precision=2), default=None, index=True)
    stop_loss = Column(Float(precision=2), default=None, index=True)
    profit_notify = Column(Boolean, default=False)
    loss_notify = Column(Boolean, default=False)
    updated = Column(DateTime, onupdate=dt.datetime.now, index=True)

    deals = relationship('Deal', backref='items', lazy='dynamic')

    def __init__(self, client_id, name, app_id=CSGO_ID, app_name=CSGO, count=0, take_profit=None,
                 stop_loss=None, profit_notify=False, loss_notify=False):
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

    def __repr__(self):
        return f"Item('{self.name}', '{self.count}')"


class Deal(Base):
    """
    Класс-отображение сущности сделки в БД.

    Attributes:
        client_id (int): ID пользователя из таблицы users
        item_id (int): ID предмета из таблицы items
        deal_type (str): Тип сделки (купля/продажа)
        price (float): Цена сделки (за один предмет)
        volume (int): Объём сделки (количество предметов с item_id)
        deal_currency (str): Валюта сделки
        date (DateTime): Дата совершения сделки (дата записи в БД)
        closed (bool) : Флаг закрытия сделки
    """
    __tablename__ = 'deals'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    client_id = Column(Integer, ForeignKey(Client.id), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey(Item.id), nullable=False, index=True)
    deal_type = Column(String, nullable=False, index=True)
    price = Column(Float(precision=2), nullable=False, index=True)
    volume = Column(Integer, nullable=False, index=True)
    deal_currency = Column(String, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    closed = Column(Boolean, default=False)

    def __init__(self, client_id, item_id, deal_type, price, volume, deal_currency, date,
                 closed=False):
        self.client_id = client_id
        self.item_id = item_id
        self.deal_type = deal_type
        self.price = price
        self.volume = volume
        self.deal_currency = deal_currency
        self.date = date
        self.closed = closed

    def __repr__(self):
        return (f"Deal('{self.deal_type}', '{self.item.name}', '{self.deal_currency}', "
                f"'{self.volume}', '{self.price}', '{self.closed}')")


class Skin(Base):
    __tablename__ = 'skins'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    skin_type = Column(String, nullable=False, index=True)
    collection = Column(String, index=True)
    name = Column(String, nullable=False, index=True)
    skin = Column(String, index=True)
    full_name = Column(String, nullable=False, index=True)
    fn = Column(Boolean, default=False)
    mw = Column(Boolean, default=False)
    ft = Column(Boolean, default=False)
    ww = Column(Boolean, default=False)
    bs = Column(Boolean, default=False)
    st = Column(Boolean, default=False)
    sv = Column(Boolean, default=False)

    quality = dict(zip(nm.WEAPON_QUALITY.keys(), [fn, mw, ft, ww, bs]))

    def __init__(self, skin_type, collection, name, skin, full_name,
                 fn=False, mw=False, ft=False, ww=False, bs=False, st=False, sv=False):
        self.skin_type = skin_type
        self.collection = collection,
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
        """Метод, который возвращает все возможные варианты имени по качеству.

        Создаётся словарь из пары значений качества и его доступности для скина.
        Затем создаётся список форматированных имён, куда подставляется значение качества, если
        скин может быть с этим качеством.

        Returns:
            List[str]: Список имён.
        """
        q_cols = dict(zip(self.quality.keys(), [self.fn, self.mw, self.ft, self.ww, self.bs]))
        names = [
            f'{self.full_name} ({nm.WEAPON_QUALITY[k]})' for k in q_cols if q_cols[k] is True
        ]
        if self.skin is None:  # Условие для ножей Vanilla(без качеств)
            names.append(self.full_name)
        return names


class Container(Base):
    __tablename__ = 'containers'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    container_type = Column(String, nullable=False, index=True)
    name = Column(String, index=True)

    def __init__(self, container_type, name):
        self.container_type = container_type
        self.name = name


class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    side = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True, unique=True)

    def __init__(self, side, name):
        self.side = side
        self.name = name


class Sticker(Base):
    __tablename__ = 'stickers'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    sticker_type = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    full_name = Column(String, nullable=False, index=True)
    collection = Column(String, index=True)
    tournament = Column(String, index=True, nullable=True, default=None)

    def __init__(self, sticker_type, name, full_name, collection, tournament=None):
        self.sticker_type = sticker_type
        self.name = name
        self.full_name = full_name
        self.collection = collection
        self.tournament = tournament


class Tool(Base):
    __tablename__ = 'tools'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    name = Column(String, nullable=False, index=True, unique=True)

    def __init__(self, name):
        self.name = name


class Price(Base):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    name = Column(String, nullable=False, index=True, unique=False, primary_key=True)
    price = Column(Float(precision=2), default=0., index=True)
    currency = Column(String, default='USD', index=True, primary_key=True)
    updated = Column(DateTime, nullable=False, index=True)

    __table_args__ = (UniqueConstraint('name', 'currency', name='_name_currency_uc'),)

    def __init__(self, name, price, updated, currency='USD'):
        self.name = name
        self.price = price
        self.currency = currency
        self.updated = updated


class PriceLimit(Base):
    __tablename__ = 'price_limits'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    currency = Column(String, index=True, unique=True)
    value = Column(Float(precision=2), default=0., index=True)
    updated = Column(DateTime, nullable=False, index=True)

    def __init__(self, currency, value, updated):
        self.currency = currency
        self.value = value
        self.updated = updated
