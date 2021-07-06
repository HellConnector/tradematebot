import datetime as dt
import gc
import os

import telegram.bot
from telegram import ParseMode, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Dispatcher,
                          Filters, JobQueue, MessageHandler, Updater, PicklePersistence)
from telegram.ext import messagequeue as mq
from telegram.utils.request import Request

import bot.db as db
import bot.deals as deals_cb
import bot.menu as menu_cb
import bot.messages as messages
import bot.names as nm
import bot.notifications as notify_cb
import bot.parsers as ps
import bot.stats as stats_cb
import bot.tracking as tracking_cb
import bot.utils as bu
from bot.logger import log
from bot.models import Client, Item, Price

TOKEN = os.getenv('BOT_TOKEN')


def start(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    username = user.first_name
    chat_id = user.id
    with db.get_session() as s:
        # Check if user already exists in database
        tmp = s.query(Client).filter(Client.chat_id == chat_id).first()
        if tmp is not None:
            tmp.name = username
            user.send_message(messages.welcome_back[tmp.lang])
        else:
            # Need for choosing language and currency during registration
            context.user_data[nm.REG_FLAG] = True
            s.add(Client(name=username, chat_id=chat_id))
            user.send_message("Hello! Choose your language by clicking button below."
                              "\n\nПривет! Выбери язык нажатием кнопки ниже.",
                              reply_markup=bu.get_inline_markup(nm.LANG))


def choose_lang(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    user.send_message("Choose your language by clicking button below."
                      "\n\nВыбери язык нажатием кнопки ниже.",
                      reply_markup=bu.get_inline_markup(nm.LANG))


def choose_currency(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    user.send_message(messages.currency_choose[lang],
                      reply_markup=bu.get_inline_markup(nm.CURRENCY))


def update_currency(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    query = update.callback_query
    currency = query.data
    with db.get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).first()
        lang = client.lang
        reg_flag = context.user_data.pop(nm.REG_FLAG, None)
        if reg_flag:
            client.currency = currency
            query.edit_message_text(messages.currency_update[lang].format(currency=currency))
        else:
            query.edit_message_text(messages.cannot_change_currency[lang])


def update_lang(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    query = update.callback_query
    with db.get_session() as s:
        reg_flag = context.user_data.get(nm.REG_FLAG, None)
        lang = query.data
        client = s.query(Client).filter(Client.chat_id == user.id).first()
        client.lang = lang
    if reg_flag:
        text = messages.reg_message[lang]
        query.edit_message_text(text, reply_markup=bu.get_inline_markup(nm.CURRENCY))
    else:
        query.edit_message_text(messages.lang_update[lang].format(lang=lang))


def help_(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    user.send_message(messages.help_message[lang], disable_web_page_preview=True,
                      reply_markup=ReplyKeyboardRemove())


def wipeout(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    with db.get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).scalar()
        if client.deals.count() == 0:
            user.send_message(messages.wipeout_no_items[lang])
        else:
            user.send_message(messages.wipeout_message[lang],
                              reply_markup=bu.get_inline_markup(buttons=("Yes", "No"), rows=1))


def wipeout_yes(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    query.edit_message_text(messages.wipeout_yes[lang],
                            reply_markup=bu.get_inline_markup(buttons=("Yes, i am sure", "NO"),
                                                              rows=1))


def wipeout_no(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    query.edit_message_text(messages.wipeout_no[lang])


def wipeout_sure(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    query = update.callback_query
    with db.get_session() as s:
        client = s.query(Client).filter(Client.chat_id == user.id).first()
        del_deals = "delete from deals where client_id=:cid"
        del_items = "delete from items where client_id=:cid"
        s.execute(del_deals, {"cid": client.id})
        s.execute(del_items, {"cid": client.id})
    log.info(f"WIPEOUT -> user [{user.id}] deleted all his deals and items")
    query.edit_message_text(messages.wipeout_sure[lang])


@bu.is_sub
def main_menu(update: Update, context: CallbackContext):
    user = bu.get_tg_user(update)
    lang = bu.get_user_lang(user)
    user.send_message(messages.menu_message[lang],
                      reply_markup=bu.get_main_menu_inline_markup())
    context.user_data.clear()
    gc.collect()

    return bu.MAIN_MENU


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    log.warning(f'Update "{update}" caused error "{context.error}"')


class MQBot(telegram.bot.Bot):

    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super().__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except Exception:
            pass

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        return super(MQBot, self).send_message(*args, parse_mode=ParseMode.MARKDOWN, **kwargs)

    @mq.queuedmessage
    def edit_message_text(self, *args, **kwargs):
        return super(MQBot, self).edit_message_text(*args, parse_mode=ParseMode.MARKDOWN, **kwargs)


def send_notifications(context: CallbackContext):
    with db.get_session() as s:
        take_profit_data = s.query(Client.chat_id, Client.currency, Item.name, Item.take_profit,
                                   Price.price).filter(
            Client.id == Item.client_id, Item.name == Price.name, Price.price > Item.take_profit,
            Client.currency == Price.currency, Item.profit_notify.is_(True)
        ).all()
        for chat_id in set(j[0] for j in take_profit_data):
            client = s.query(Client).filter(Client.chat_id == chat_id).scalar()
            items_data = [i[1:] for i in filter(lambda x: x[0] == chat_id, take_profit_data)]
            items_str = '\n'.join(f'{i + 1}) `{bu.get_short_name(d[1])}`:\n`{d[2]} {d[0]}` -> '
                                  f'`{d[3]} {d[0]}`' for i, d in enumerate(items_data))
            message = f"{messages.notify_take_profit_reached[client.lang]}{items_str}"

            # Sending message
            context.bot.send_message(chat_id=chat_id, text=message,
                                     reply_markup=ReplyKeyboardRemove())

            # Turning notification flag to False
            client_items = client.items.filter(Item.name.in_(x[1] for x in items_data)).all()
            for item in client_items:
                item.profit_notify = False


def update_price_limits(context: CallbackContext):
    bu.update_price_limits()


def main():
    q = mq.MessageQueue(all_burst_limit=30, all_time_limit_ms=1000)
    request = Request(con_pool_size=8)
    bot = MQBot(token=TOKEN, request=request, mqueue=q)
    persistence = PicklePersistence(filename='persistence')
    updater = Updater(bot=bot, persistence=persistence)
    dp: Dispatcher = updater.dispatcher
    job: JobQueue = updater.job_queue
    job.run_repeating(send_notifications, interval=3600, first=dt.datetime(year=2021, day=1,
                                                                           month=7, minute=45))
    job.run_daily(update_price_limits, time=dt.time(hour=3, minute=33))

    pattern_func = [
        (bu.w_pattern, ps.parse_weapon_text),
        (bu.g_pattern, ps.parse_glove_text),
        (bu.c_pattern, ps.parse_container_text),
        (bu.k_pattern, ps.parse_knife_text),
        (bu.a_pattern, ps.parse_agent_text),
        (bu.s_pattern, ps.parse_sticker_text),
        (bu.p_pattern, ps.parse_patch_text),
        (bu.t_pattern, ps.parse_tool_text)
    ]

    skin_handlers = (
        MessageHandler(Filters.regex(p), deals_cb.get_item_function(p, f)) for p, f in pattern_func
    )

    menu_handler = CommandHandler('menu', main_menu)

    choose_currency_handler = CommandHandler('setcurrency', choose_currency)
    update_currency_handler = CallbackQueryHandler(update_currency,
                                                   pattern=rf'^({"|".join(nm.CURRENCY)})$')

    choose_lang_handler = CommandHandler('setlang', choose_lang)
    update_lang_handler = CallbackQueryHandler(update_lang, pattern=r'^(RU|EN)$')

    conv_handler = ConversationHandler(
        persistent=True,
        name='conv_handler',
        entry_points=[
            menu_handler
        ],
        states={
            bu.MAIN_MENU: [
                CallbackQueryHandler(menu_cb.deals, pattern=r'^Deals$'),
                CallbackQueryHandler(menu_cb.stats, pattern=r'^Stats$'),
                CallbackQueryHandler(menu_cb.tracking, pattern=r'^Tracking$'),
                CallbackQueryHandler(menu_cb.notifications, pattern=r'^Notifications$')
            ],

            bu.DEALS: [
                CallbackQueryHandler(deals_cb.set_deal_type, pattern=r'^(Buy|Sell)$')
            ],

            bu.ITEMS: [
                *skin_handlers,
                MessageHandler(Filters.regex(bu.selected_item_pattern), deals_cb.selected_item),
                MessageHandler(Filters.regex(bu.cp_pattern), deals_cb.item_count_price),
                MessageHandler(Filters.regex(r'(?!menu\b)\b\w+'), deals_cb.unknown_query)
            ],

            bu.STATS: [
                CallbackQueryHandler(stats_cb.get_items_stats, pattern=r'^(Newest|%|Value)$')
            ],

            bu.TRACKING: [
                CallbackQueryHandler(tracking_cb.get_tracking_table, pattern=r'^(%|Value)$')
            ],

            bu.NOTIFICATIONS: [
                CallbackQueryHandler(notify_cb.show_items_notify,
                                     pattern=rf'^({"|".join(nm.NOTIFY_TYPES)})$'),
                CallbackQueryHandler(notify_cb.change_page, pattern=r'^(<<<|>>>){1}$'),
                CallbackQueryHandler(notify_cb.choose_item, pattern=r'^[0-7]{1}$'),
                CallbackQueryHandler(notify_cb.cancel, pattern=r'Cancel'),
                MessageHandler(Filters.regex(bu.notify_pattern), notify_cb.take_profit)
            ]
        },
        fallbacks=[
            menu_handler
        ]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help_))
    dp.add_handler(CommandHandler('wipeout', wipeout))
    dp.add_handler(CallbackQueryHandler(wipeout_yes, pattern=r'^Yes$'))
    dp.add_handler(CallbackQueryHandler(wipeout_no, pattern=r'^(No|NO){1}$'))
    dp.add_handler(CallbackQueryHandler(wipeout_sure, pattern=r'^Yes, i am sure$'))
    dp.add_handler(choose_currency_handler)
    dp.add_handler(choose_lang_handler)
    dp.add_handler(update_currency_handler)
    dp.add_handler(update_lang_handler)
    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.text, help_))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
