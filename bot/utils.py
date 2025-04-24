import datetime as dt
import re
from enum import Enum
from functools import wraps
from typing import List, Tuple, Union, Dict

import httpx
import math
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import ChatMember, WebAppInfo
from telegram import (
    Update,
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import ContextTypes

from bot import constants, messages, settings
from bot.db import Client, PriceLimit, get_async_session
from bot.logger import log


class State(Enum):
    MAIN_MENU = 0
    DEALS = 1
    ITEMS = 2
    NOTIFICATIONS = 3


ALLOWED_USERS_STATUS = (
    ChatMember.MEMBER,
    ChatMember.OWNER,
    ChatMember.ADMINISTRATOR,
)


def get_pattern(regex: str) -> re.Pattern:
    return re.compile(regex, re.IGNORECASE)


items_per_page = 8

w_pattern = get_pattern(r"^w\s+[\w\W]+\s+(fn|mw|ft|ww|bs){1}\s*(st|sv)?")
g_pattern = get_pattern(r"^g [\w\W ]+ (fn|mw|ft|ww|bs){1} *$")
c_pattern = get_pattern(r"^c +[\w\W ]+")
k_pattern = get_pattern(r"^k +[\w\W]+ *(fn|mw|ft|ww|bs)? *(st)? *")
s_pattern = get_pattern(r"^s +[\w\W ]+ *$")
p_pattern = get_pattern(r"^p +[\w\W ]+ *$")
a_pattern = get_pattern(r"^a\s+(t|ct)?\s*[\w\W]+")
t_pattern = get_pattern(r"^t +[\w\W ]+")
selected_item_pattern = get_pattern(r"^\d+$")
cp_pattern = get_pattern(r"^\d+\s+\d*(\.|\,)?\d{0,3}")
notify_pattern = get_pattern(r"^\d*(\.|\,)?\d{0,3}$")


async def get_tg_user(update: Update) -> User:
    if update.message is not None:
        user: User = update.message.from_user
        log.info(
            f"Client [{user.id} -> @{user.username} -> "
            f"{user.first_name}] send [{update.message.text}]"
        )
    else:
        user: User = update.callback_query.from_user
        log.info(
            f"Client [{user.id} -> @{user.username} -> "
            f"{user.first_name}] send [{update.callback_query.data}]"
        )
        await update.callback_query.answer()
    return user


def inject_db_session_and_client(callback):
    @wraps(callback)
    async def inner(*args, **kwargs):
        update, context = args
        async with get_async_session() as session:
            user = await get_tg_user(update)
            client = await session.scalar(
                select(Client).where(Client.chat_id == user.id)
            )
            args = (*args, user, session, client)
            return await callback(*args, **kwargs)

    return inner


def get_inline_markup(
    buttons: Union[List, Tuple], rows=1
) -> InlineKeyboardMarkup:
    if not 1 <= rows <= len(buttons):
        raise ValueError(
            "Rows count can not be less than 1 and more than buttons count."
        )
    cols = math.ceil(len(buttons) / rows)
    last_row_count = len(buttons) - (cols * (rows - 1))
    keyboard = [
        [
            InlineKeyboardButton(
                str(buttons[i * cols + j]),
                callback_data=str(buttons[i * cols + j]),
            )
            for j in range(cols)
        ]
        for i in range(rows - 1)
    ]
    keyboard.append(
        [
            InlineKeyboardButton(str(b), callback_data=str(b))
            for b in buttons[-last_row_count:]
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def get_inline_markup_keyboard_row(
    buttons: Union[List, Tuple],
) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(button, callback_data=button)
        for button in buttons
    ]


def get_main_menu_inline_markup() -> InlineKeyboardMarkup:
    web_app_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            get_inline_markup_keyboard_row(["Deals", "Notifications"]),
            [
                InlineKeyboardButton(
                    "Portfolio",
                    web_app=WebAppInfo(
                        url=f"{settings.MINI_APP_URL}/portfolio/"
                    ),
                ),
                InlineKeyboardButton(
                    "Stats",
                    web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/stats/"),
                ),
                InlineKeyboardButton(
                    "History",
                    web_app=WebAppInfo(
                        url=f"{settings.MINI_APP_URL}/history/"
                    ),
                ),
            ],
        ]
    )
    return web_app_markup


def get_items_keyboard(user_data: Dict) -> InlineKeyboardMarkup:
    page_num = user_data[constants.PAGE_NUM]
    keyboard = [
        [
            InlineKeyboardButton(f"{i + 1}", callback_data=f"{i}")
            for i in range(len(user_data[constants.PAGES][page_num]))
        ],
        [
            InlineKeyboardButton("<<<", callback_data="<<<"),
            InlineKeyboardButton(">>>", callback_data=">>>"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_items_text(user_data: Dict) -> str:
    page_num = user_data[constants.PAGE_NUM]
    page_count = user_data[constants.PAGE_COUNT]
    page = user_data[constants.PAGES][page_num]
    return f"`{page_num + 1}/{page_count}`:\n" + "\n".join(
        map(lambda x: f"`{x[0] + 1}) {x[1]}`", enumerate(page))
    )


def get_short_name(item_name: str):
    ret_value = ""
    for key, value in constants.WEAPON_QUALITY.items():
        if value in item_name:
            ret_value = item_name.replace(value, key.upper())
    if constants.ST in ret_value:
        ret_value = ret_value.replace(constants.ST, "ST")
    if constants.SV in ret_value:
        ret_value = ret_value.replace(constants.ST, "SV")
    return ret_value if ret_value else item_name


def is_sub(callback):
    @wraps(callback)
    async def inner(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        session: AsyncSession,
        client: Client,
    ):
        chat_member = await context.bot.get_chat_member(
            chat_id=settings.CHANNEL_ID, user_id=user.id
        )
        if chat_member.status in ALLOWED_USERS_STATUS:
            return await callback(update, context, user, session, client)
        else:
            log.info(
                (
                    f"Client [{user.id} -> @{user.username} -> {user.first_name}] "
                    f"is not subscriber"
                )
            )
            await user.send_message(
                messages.subscriber_message[client.lang],
                disable_web_page_preview=True,
            )

    return inner


async def update_price_limits() -> dict | None:
    url = (
        f"https://api.apilayer.com/fixer/latest?"
        f"base=EUR&symbols={','.join(constants.CURRENCY)}"
    )
    headers = {"apikey": settings.CURRENCY_API_KEY}
    try:
        async with httpx.AsyncClient() as client:
            response = (
                await client.get(url, timeout=15, headers=headers)
            ).json()
    except httpx.TimeoutException:
        log.exception("Failed to receive currency rates from fixer.io")
        return
    except ValueError:
        log.exception("Failed to parse response JSON")
        return
    if message := response.get("message"):
        if "You have exceeded your daily/monthly API rate limit" in message:
            return
    limits_to_return = {"price_limits": {}}
    rates: Dict = response.get("rates")
    if rates:
        if rates["USD"] == 0:
            log.info(
                "Failed to parse currency rates -> USD rate equals to zero"
            )
            return
        async with get_async_session() as session:
            price_limits = (await session.scalars(select(PriceLimit))).all()
            for currency, rate in rates.items():
                value = round(2000 * rate / rates["USD"], 2)
                price_limit = next(
                    filter(lambda p: p.currency == currency, price_limits),
                    None,
                )
                if price_limit is None:
                    session.add(PriceLimit(currency, value, dt.datetime.now()))
                else:
                    price_limit.value = value
                    price_limit.updated = dt.datetime.now()
                limits_to_return["price_limits"][currency] = value
        log.info("Price limits update is completed")
        return limits_to_return
