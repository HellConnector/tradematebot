import datetime as dt
import gc
from warnings import filterwarnings

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import (
    ReplyKeyboardRemove,
    Update,
    User,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    JobQueue,
    MessageHandler,
    ContextTypes,
    filters,
    Defaults,
)
from telegram.warnings import PTBUserWarning

from bot import (
    constants,
    deals,
    menu,
    messages,
    notifications,
    parsers,
    settings,
    utils,
)
from bot.db import Client, Deal, Item
from bot.jobs import (
    update_price_limits,
    send_notifications,
    update_tracking_records,
)
from bot.logger import log

filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


@utils.inject_db_session_and_client
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    username = user.first_name
    chat_id = user.id
    # Check if user already exists in database
    if client is not None:
        client.name = username
        await user.send_message(messages.welcome_back[client.lang])
    else:
        # Need to choose language and currency during registration
        context.user_data[constants.REG_FLAG] = True
        session.add(Client(name=username, chat_id=chat_id))
        await user.send_message(
            "Hello! Choose your language by clicking button below."
            "\n\nПривет! Выбери язык нажатием кнопки ниже.",
            reply_markup=utils.get_inline_markup(constants.LANG),
        )


@utils.inject_db_session_and_client
async def choose_currency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    await user.send_message(
        messages.currency_choose[client.lang],
        reply_markup=utils.get_inline_markup(constants.CURRENCY),
    )


async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await utils.get_tg_user(update)
    await user.send_message(
        "Choose your language by clicking button below."
        "\n\nВыбери язык нажатием кнопки ниже.",
        reply_markup=utils.get_inline_markup(constants.LANG),
    )


@utils.inject_db_session_and_client
async def update_currency(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    currency = query.data
    reg_flag = context.user_data.pop(constants.REG_FLAG, None)
    if reg_flag:
        client.currency = currency
        await query.edit_message_text(
            messages.currency_update[client.lang].format(currency=currency)
        )
    else:
        await query.edit_message_text(
            messages.cannot_change_currency[client.lang]
        )


@utils.inject_db_session_and_client
async def update_lang(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    reg_flag = context.user_data.get(constants.REG_FLAG, None)
    lang = query.data
    client.lang = lang
    if reg_flag:
        text = messages.reg_message[lang]
        await query.edit_message_text(
            text, reply_markup=utils.get_inline_markup(constants.CURRENCY)
        )
    else:
        await query.edit_message_text(
            messages.lang_update[lang].format(lang=lang)
        )


@utils.inject_db_session_and_client
async def help_(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    await user.send_message(
        messages.help_message[client.lang],
        disable_web_page_preview=True,
        reply_markup=ReplyKeyboardRemove(),
    )


@utils.inject_db_session_and_client
async def wipeout(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    deals_count = await session.scalar(
        select(func.count(Deal.id)).where(Deal.client_id == client.id)
    )

    if deals_count == 0:
        await user.send_message(messages.wipeout_no_items[client.lang])
    else:
        await user.send_message(
            messages.wipeout_message[client.lang],
            reply_markup=utils.get_inline_markup(
                buttons=("Yes", "No"), rows=1
            ),
        )


@utils.inject_db_session_and_client
async def wipeout_yes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    await query.edit_message_text(
        messages.wipeout_yes[client.lang],
        reply_markup=utils.get_inline_markup(
            buttons=("Yes, i am sure", "NO"), rows=1
        ),
    )


@utils.inject_db_session_and_client
async def wipeout_no(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    await query.edit_message_text(messages.wipeout_no[client.lang])


@utils.inject_db_session_and_client
async def wipeout_sure(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    query = update.callback_query
    await session.execute(delete(Deal).where(Deal.client_id == client.id))
    await session.execute(delete(Item).where(Item.client_id == client.id))
    log.info(f"WIPEOUT -> user [{user.id}] deleted all his deals and items")
    await query.edit_message_text(messages.wipeout_sure[client.lang])


@utils.inject_db_session_and_client
@utils.is_sub
async def main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    session: AsyncSession,
    client: Client,
):
    await user.send_message(
        messages.menu_message[client.lang],
        reply_markup=utils.get_main_menu_inline_markup(),
    )
    context.user_data.clear()
    gc.collect()

    return utils.State.MAIN_MENU


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    log.warning(f'Update "{update}" caused error "{context.error}"')


def run():
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN)

    bot = (
        Application.builder()
        .token(settings.BOT_TOKEN)
        .defaults(defaults=defaults)
        .concurrent_updates(True)
        .build()
    )

    job: JobQueue = bot.job_queue
    job.run_repeating(
        send_notifications,
        interval=3600,
    )

    job.run_daily(update_price_limits, time=dt.time(hour=3, minute=33))
    job.run_once(update_price_limits, when=0)
    job.run_repeating(update_tracking_records, interval=3600, first=15)

    pattern_func = [
        (utils.w_pattern, parsers.parse_weapon_text),
        (utils.g_pattern, parsers.parse_glove_text),
        (utils.c_pattern, parsers.parse_container_text),
        (utils.k_pattern, parsers.parse_knife_text),
        (utils.a_pattern, parsers.parse_agent_text),
        (utils.s_pattern, parsers.parse_sticker_text),
        (utils.p_pattern, parsers.parse_patch_text),
        (utils.t_pattern, parsers.parse_tool_text),
    ]

    skin_handlers = (
        MessageHandler(
            filters.Regex(pattern), deals.get_item_function(pattern, function)
        )
        for pattern, function in pattern_func
    )

    menu_handler = CommandHandler("menu", main_menu)

    choose_currency_handler = CommandHandler("setcurrency", choose_currency)
    update_currency_handler = CallbackQueryHandler(
        update_currency, pattern=rf"^({'|'.join(constants.CURRENCY)})$"
    )

    choose_lang_handler = CommandHandler("setlang", choose_lang)
    update_lang_handler = CallbackQueryHandler(
        update_lang, pattern=r"^(RU|EN)$"
    )

    conv_handler = ConversationHandler(
        name="conv_handler",
        entry_points=[menu_handler],
        states={
            utils.State.MAIN_MENU: [
                CallbackQueryHandler(menu.deals, pattern=r"^Deals$"),
                CallbackQueryHandler(
                    menu.notifications, pattern=r"^Notifications$"
                ),
            ],
            utils.State.DEALS: [
                CallbackQueryHandler(
                    deals.set_deal_type, pattern=r"^(Buy|Sell)$"
                )
            ],
            utils.State.ITEMS: [
                *skin_handlers,
                MessageHandler(
                    filters.Regex(utils.selected_item_pattern),
                    deals.selected_item,
                ),
                MessageHandler(
                    filters.Regex(utils.cp_pattern), deals.item_count_price
                ),
                MessageHandler(
                    filters.Regex(r"(?!menu\b)\b\w+"), deals.unknown_query
                ),
            ],
            utils.State.NOTIFICATIONS: [
                CallbackQueryHandler(
                    notifications.show_items,
                    pattern=rf"^({'|'.join(constants.NOTIFY_TYPES)})$",
                ),
                CallbackQueryHandler(
                    notifications.change_page, pattern=r"^(<<<|>>>){1}$"
                ),
                CallbackQueryHandler(
                    notifications.choose_item, pattern=r"^[0-7]{1}$"
                ),
                CallbackQueryHandler(notifications.cancel, pattern=r"Cancel"),
                MessageHandler(
                    filters.Regex(utils.notify_pattern),
                    notifications.take_profit,
                ),
            ],
        },
        fallbacks=[menu_handler],
    )

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("help", help_))
    bot.add_handler(CommandHandler("wipeout", wipeout))
    bot.add_handler(CallbackQueryHandler(wipeout_yes, pattern=r"^Yes$"))
    bot.add_handler(CallbackQueryHandler(wipeout_no, pattern=r"^(No|NO){1}$"))
    bot.add_handler(
        CallbackQueryHandler(wipeout_sure, pattern=r"^Yes, i am sure$")
    )
    bot.add_handler(choose_currency_handler)
    bot.add_handler(choose_lang_handler)
    bot.add_handler(update_currency_handler)
    bot.add_handler(update_lang_handler)
    bot.add_handler(conv_handler)
    bot.add_handler(MessageHandler(filters.TEXT, help_))

    bot.add_error_handler(error)

    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run()
