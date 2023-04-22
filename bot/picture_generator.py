import math
from datetime import date, datetime
from io import BytesIO
from typing import List

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import case, desc, func, select
from sqlalchemy.sql import label

import constants
from db import Client, Deal, Item, Price

font_path = "resources/RobotoMono-Medium.ttf"
no_price_loading = "loading "


async def get_tracking_data(chat_id, currency, session):
    item_limit = await session.scalar(
        select(Client.item_limit).where(Client.chat_id == chat_id)
    )
    client_deals = await session.execute(
        select(
            func.min(Deal.date),
            Item.name,
            Item.count,
            func.sum(Deal.price * Deal.volume)
            / func.sum(Deal.volume).label("avg_price"),
            Price.price,
            Deal.deal_currency,
        )
        .where(
            Client.chat_id == chat_id,
            Deal.client_id == Client.id,
            Deal.deal_type == "buy",
            Deal.closed.is_(False),
            Deal.item_id == Item.id,
            Item.name == Price.name,
            Item.client_id == Client.id,
            Item.count > 0,
            Deal.deal_currency == Price.currency,
            Deal.deal_currency == currency,
        )
        .group_by(Deal.item_id, Item.name, Price.price, Item.count, Deal.deal_currency)
        .limit(item_limit)
    )

    deals = []

    for d_date, name, count, buy, price, currency in client_deals:
        # hold days
        deal_date = datetime.date(d_date)
        current_date = datetime.strptime(date.today().isoformat(), "%Y-%m-%d").date()
        delta_days = current_date - deal_date

        # income in percent
        price_with_tax = price * 0.87
        try:
            income_percent = (price_with_tax - buy) / buy * 100
        except ZeroDivisionError:
            income_percent = price_with_tax

        # income in currency
        income_money = (price_with_tax - buy) * count

        deals.append(
            [
                delta_days.days,
                name,
                count,
                currency,
                buy,
                price,
                income_percent,
                income_money,
            ]
        )

    return deals


def format_for_tracking(sorted_deals):
    for deal in sorted_deals:
        # hold days
        deal[0] = get_format_cell(int(deal[0]), 4, "right")

        # Item name in Steam market
        deal[1] = format_item_name(deal[1])

        # Number of items in a deal
        deal[2] = get_format_cell(int(deal[2]), 5, "right")

        # Deal price
        deal[4] = round(deal[4], 2)
        deal[4] = get_format_cell(deal[4], 9, "right")

        # Price in market (if price is not loaded we show 'loading')
        if deal[5] == 0:
            no_price = True
            deal[5] = no_price_loading
        else:
            no_price = False
            deal[5] = round(deal[5], 2)
        deal[5] = get_format_cell(deal[5], 9, "right")

        # Income percent
        deal[6] = round(deal[6], 1)
        if deal[6] > 0:
            deal[3] = "green"
            deal[6] = get_format_cell("+" + str(deal[6]), 9, "right")
        elif no_price:
            deal[3] = "gray"
            deal[6] = no_price_loading
            deal[6] = get_format_cell(deal[6], 9, "right")
        else:
            deal[3] = "red"
            deal[6] = get_format_cell(deal[6], 9, "right")

        # Income sum
        deal[7] = round(deal[7], 1)
        if deal[7] > 0:
            deal[7] = get_format_cell("+" + str(deal[7]), 10, "right")
        elif no_price:
            deal[7] = no_price_loading
            deal[7] = get_format_cell(deal[7], 10, "right")
        else:
            deal[7] = get_format_cell(deal[7], 10, "right")

    return sorted_deals


async def get_tracking_pic(chat_id, currency, sort_key, s):
    client_deals = await get_tracking_data(chat_id, currency, s)

    # Sort deals
    sort_index = 7 if sort_key == "Value" else 6

    # index=6 - income(%), index=7 - income($)
    client_deals.sort(key=lambda x: x[sort_index], reverse=True)

    # Calculate all spent, cost, profit
    spent, cost, profit = 0, 0, 0
    for deal in client_deals:
        spent += deal[2] * deal[4]
        if deal[5] > 0:
            cost += deal[2] * deal[5]
            profit += deal[7]
    spent, cost, profit = round(spent, 1), round(cost, 1), round(profit, 1)

    # Formatting for image
    client_deals = format_for_tracking(client_deals)

    # Image constants
    line_height = 22
    img_width = 612
    deals_limit_on_pic = 48
    bottom_height = 44

    # Items limit per page = 48
    if len(client_deals) <= deals_limit_on_pic:
        need_pictures = 1
    else:
        need_pictures = math.ceil(len(client_deals) / deals_limit_on_pic)
    number_of_picture = 0
    pictures = []

    while number_of_picture < need_pictures:
        number_of_picture += 1
        line_num = 1
        img_height = (
            len(client_deals[:deals_limit_on_pic]) * line_height
            + line_height
            + 3
            + bottom_height
        )
        img = Image.new("RGBA", (img_width, img_height), color="white")
        fnt = ImageFont.truetype(font_path, 10, encoding="unic")
        d = ImageDraw.Draw(img)

        # Header
        d.text(
            (0, 0),
            "               Generated by t.me/TradeMateBot      "
            "                                                   ",
            font=fnt,
            fill="red",
        )
        d.text(
            (0, 0),
            "Hold                                                    "
            "Qty         Price               Income        ",
            font=fnt,
            fill="black",
        )
        d.text(
            (0, 0), " " * 98 + "[#" + str(number_of_picture) + "]", font=fnt, fill="red"
        )
        d.text(
            (0, (line_height / 2) + 2),
            f"Days                     Item Name                       "
            f"#      Buy       Now        %         {currency}    ",
            font=fnt,
            fill="black",
        )

        d.line((25, 0) + (25, img_height - bottom_height), fill="gray")
        d.line((327, 0) + (327, img_height - bottom_height), fill="gray")
        d.line((362, 0) + (362, img_height - bottom_height), fill="gray")
        d.line((423, 13) + (423, img_height - bottom_height), fill="gray")
        d.line((483, 0) + (483, img_height - bottom_height), fill="gray")
        d.line((542, 13) + (542, img_height - bottom_height), fill="gray")

        for deal in client_deals[:deals_limit_on_pic]:
            if deal[3] == "red":
                color = "red"
            elif deal[3] == "gray":
                color = "gray"
            else:
                color = "green"

            # Add deals on page  (2 rows, first - delimiter, second - item info
            d.line(
                (0, line_num * line_height + 5)
                + (img_width, line_num * line_height + 5),
                fill="gray",
                width=2,
            )

            d.text(
                (0, line_num * line_height + line_height / 2),
                f"{deal[0]} {deal[1]} {deal[2]} {deal[4]} "
                f"{deal[5]} {deal[6]} {deal[7]}",
                font=fnt,
                fill=color,
            )
            line_num += 1

        del client_deals[:deals_limit_on_pic]

        # Add delimiter for footer
        d.line(
            (0, line_num * line_height + 5) + (img_width, line_num * line_height + 5),
            fill="gray",
            width=2,
        )

        # Results in footer {Total spent: } {cost: } {profit: }
        total_without_colored_profit = (
            f"Total spent: {spent} | Current value: " f"{cost} | Total profit: "
        )
        profit_color = "red" if profit < 0 else "green"

        d.text(
            (line_height / 2, line_num * line_height + line_height - 4),
            total_without_colored_profit,
            font=ImageFont.truetype(font_path, 14),
            fill="black",
        )

        d.text(
            (line_height / 2, line_num * line_height + line_height - 3),
            f'{len(total_without_colored_profit) * " "}{profit}',
            font=ImageFont.truetype(font_path, 14),
            fill=profit_color,
        )

        # Save image in memory
        bio = BytesIO()
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bio.name = f"tracking_{number_of_picture}_{time}.png"
        img.save(bio, "PNG")
        bio.seek(0)

        pictures.append(bio)

    return pictures


async def get_stats_data(client_id, currency, sort_key, s) -> List:
    income_abs = "income_abs"
    income_prc = "income_prc"

    if sort_key == "Value":
        sort_label = income_abs
    elif sort_key == "Newest":
        sort_label = "sell_date"
    else:
        sort_label = income_prc

    ie = (
        select(
            Deal.item_id,
            Item.name.label("item_name"),
            func.max(Deal.date).label("sell_date"),
            func.sum(Deal.volume).label("sell_count"),
            func.sum(Deal.volume * Deal.price).label("earned_by_item"),
            label(
                "avg_sell_price",
                func.sum(Deal.price * Deal.volume) / func.sum(Deal.volume),
            ),
        )
        .where(
            Item.id == Deal.item_id,
            Deal.client_id == client_id,
            Deal.deal_type == "sell",
            Deal.deal_currency == currency,
        )
        .group_by(Deal.item_id, Item.name)
    )

    ie = ie.cte("items_earned")
    ib = (
        select(
            ie.c.item_id,
            func.min(Deal.date).label("buy_date"),
            func.sum(Deal.volume).label("buy_count"),
            func.sum(Deal.volume * Deal.price).label("spent_by_item"),
            label(
                "avg_buy_price",
                func.sum(Deal.price * Deal.volume) / func.sum(Deal.volume),
            ),
        )
        .where(
            ie.c.item_id == Deal.item_id,
            Deal.client_id == client_id,
            Deal.deal_type == "buy",
            Deal.deal_currency == currency,
        )
        .group_by(ie.c.item_id)
    )
    ib = ib.cte("items_buy")
    stats = (
        select(
            ie.c.item_name,
            func.date_part("day", ie.c.sell_date - ib.c.buy_date).label("hold_days"),
            label("left_count", ib.c.buy_count - ie.c.sell_count),
            ib.c.buy_count,
            ib.c.avg_buy_price,
            ib.c.spent_by_item,
            ie.c.sell_count,
            ie.c.avg_sell_price,
            ie.c.earned_by_item,
            label(income_abs, ie.c.earned_by_item - ib.c.spent_by_item),
            label(
                income_prc,
                (
                    ie.c.earned_by_item
                    / case((ib.c.spent_by_item == 0.0, 1), else_=ib.c.spent_by_item)
                    - 1
                )
                * 100,
            ),
        )
        .where(ie.c.item_id == ib.c.item_id)
        .order_by(desc(sort_label))
    )

    return (await s.execute(stats)).all()


def format_for_stats(data):
    result = []
    for deal in data:
        temp = []

        # [Item Name]
        temp.append(format_item_name(deal.item_name))

        # [Hold Days]
        temp.append(get_format_cell(int(deal.hold_days), 4, "right"))

        # [Items Left]
        temp.append(get_format_cell(deal.left_count, 5, "right"))

        # [Buy - #]
        temp.append(get_format_cell(deal.buy_count, 5, "right"))

        # [Buy - Price]
        temp.append(get_format_cell(round(deal.avg_buy_price, 2), 9, "right"))

        # [Buy - Total]
        temp.append(get_format_cell(round(deal.spent_by_item, 2), 9, "right"))

        # [Sell - #]
        temp.append(get_format_cell(deal.sell_count, 5, "right"))

        # [Sell - Price]
        temp.append(get_format_cell(round(deal.avg_sell_price, 2), 9, "right"))

        # [Sell - Total
        temp.append(get_format_cell(round(deal.earned_by_item, 2), 9, "right"))

        # Income in %
        temp.append(get_format_cell(round(deal.income_prc, 1), 9, "right"))

        # Income in $
        temp.append(get_format_cell(round(deal.income_abs, 1), 9, "right"))

        # Income flag for color
        if deal.income_abs > 0:
            temp.append("green")
        else:
            temp.append("red")

        result.append(temp)
    return result


async def get_stats_pic(client_id, currency, sort_key, s):
    client_stats = await get_stats_data(client_id, currency, sort_key, s)

    # Calculation all spent, cost, profit
    spent, sold, profit = 0, 0, 0
    for deal in client_stats:
        spent += deal[5]
        sold += deal[8]
        profit += deal[9]
    spent, sold, profit = round(spent, 1), round(sold, 1), round(profit, 1)

    # Formatting for image
    client_stats = format_for_stats(client_stats)

    # Constants for stats image
    line_height = 22
    img_width = 795
    deals_limit_on_pic = 48
    bottom_height = 44

    # Items limit on image = 48
    if len(client_stats) <= deals_limit_on_pic:
        need_pictures = 1
    else:
        need_pictures = math.ceil(len(client_stats) / deals_limit_on_pic)
    number_of_picture = 0
    pictures = []

    while number_of_picture < need_pictures:
        number_of_picture += 1
        line_num = 1
        img_height = (
            len(client_stats[:deals_limit_on_pic]) * line_height
            + line_height
            + 3
            + bottom_height
        )
        img = Image.new("RGBA", (img_width, img_height), color="white")
        fnt = ImageFont.truetype(font_path, 10, encoding="unic")
        d = ImageDraw.Draw(img)

        # Header
        d.text((0, 0), "          Generated by t.me/TradeMateBot", font=fnt, fill="red")
        d.text(
            (0, 0),
            "                                                  "
            "Hold Items            BUY                      SELL                   INCOME",
            font=fnt,
            fill="black",
        )
        d.text(
            (0, 0),
            " " * 128 + "[#" + str(number_of_picture) + "]",
            font=fnt,
            fill="red",
        )
        d.text(
            (0, (line_height / 2) + 2),
            f"                    Item Name                     "
            f"Days Left    #     Price     Total     #     Price     Total       %        "
            f"{currency}",
            font=fnt,
            fill="black",
        )

        d.line((297, 0) + (297, img_height - bottom_height), fill="black", width=2)
        d.line((328, 0) + (328, img_height - bottom_height), fill="black", width=2)
        d.line((364, 0) + (364, img_height - bottom_height), fill="black", width=2)
        d.line((400, 13) + (400, img_height - bottom_height), fill="black")
        d.line((459, 13) + (459, img_height - bottom_height), fill="black")
        d.line((520, 0) + (520, img_height - bottom_height), fill="black", width=2)
        d.line((364, 12) + (795, 12), fill="black")
        d.line((556, 13) + (556, img_height - bottom_height), fill="black")
        d.line((616, 13) + (616, img_height - bottom_height), fill="black")
        d.line((676, 0) + (676, img_height - bottom_height), fill="black", width=2)
        d.line((737, 13) + (737, img_height - bottom_height), fill="black")

        for deal in client_stats[:deals_limit_on_pic]:
            if deal[11] == "red":
                color = "red"
            else:
                color = "green"

            d.line(
                (0, line_num * line_height + 5)
                + (img_width, line_num * line_height + 5),
                fill="black",
            )

            d.text(
                (2, line_num * line_height + line_height / 2),
                f"{deal[0]} {deal[1]} {deal[2]} {deal[3]} "
                f"{deal[4]} {deal[5]} {deal[6]} {deal[7]} "
                f"{deal[8]} {deal[9]} {deal[10]}",
                font=fnt,
                fill=color,
            )
            line_num += 1

        del client_stats[:deals_limit_on_pic]

        d.line(
            (0, line_num * line_height + 5) + (img_width, line_num * line_height + 5),
            fill="black",
            width=3,
        )

        total_without_colored_profit = f"Spent: {spent} | Sold: " f"{sold} | Profit: "
        profit_color = "red" if profit < 0 else "green"

        d.text(
            (line_height * 14, line_num * line_height + line_height - 4),
            total_without_colored_profit,
            font=ImageFont.truetype(font_path, 14),
            fill="black",
        )

        d.text(
            (line_height * 14, line_num * line_height + line_height - 3),
            f'{len(total_without_colored_profit) * " "}{profit}',
            font=ImageFont.truetype(font_path, 14),
            fill=profit_color,
        )

        bio = BytesIO()
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bio.name = f"stats_{number_of_picture}_{time}.png"

        img.save(bio, "PNG")
        bio.seek(0)
        pictures.append(bio)

    return pictures


def format_item_name(item_name):
    item_name = (
        item_name.replace(" | ", "-")
        .replace(constants.STAR + " ", "")
        .replace(constants.ST, "(ST)")
        .replace(constants.SV, "(SV)")
        .replace("Factory New", "FN")
        .replace("Minimal Wear", "MW")
        .replace("Field-Tested", "FT")
        .replace("Well-Worn", "WW")
        .replace("Battle-Scarred", "BS")
    )
    if len(item_name) > 49:
        item_name = f"{item_name[:47]}.."
    item_name = f'{item_name}{" " * (49 - len(item_name))}'
    return item_name


def get_format_cell(value, cell_size, align):
    if align == "left":
        value = f'{value}{" " * (cell_size - len(str(value)))}'
    if align == "right":
        value = f'{" " * (cell_size - len(str(value)))}{value}'
    return value


if __name__ == "__main__":
    pass
