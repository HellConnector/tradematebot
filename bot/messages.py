RU = 'RU'
EN = 'EN'

lang_update = {
    RU: "Язык изменён на `{lang}`."
        "\n\nНаберите /menu чтобы продолжить.",

    EN: "Language is changed to `{lang}`."
        "\n\nEnter /menu to continue."
}

currency_update = {
    RU: "Валюта изменена на `{currency}`."
        "\n\nНаберите /menu чтобы продолжить.",

    EN: "Your currency is changed to `{currency}`."
        "\n\nEnter /menu to continue."
}

currency_choose = {
    RU: "Выберите валюту нажатием кнопки ниже.",

    EN: "Choose your currency by clicking button below."
}

reg_message = {
    RU: "Добро пожаловать в TradeMateBot! \U0001F916"
        "\n\nЭтот бот поможет вам с с вашими CS:GO инвестициями"
        "\U0001F4B0\n\nЧто я могу? \U0001F3AF"
        "\n\n- Я могу запоминать все твои сделки, теперь ты ничего не упустишь."
        "\U0001F4DD\nНапример, когда ты что-то продаешь или покупаешь, просто дай мне знать, "
        "и я запомню все что нужно\U0001F60E\U0001F4AD "
        "\n\n- Я могу отслеживать все цены и твою прибыль в реальном времени,"
        "а ты расслабься и предоставь всю суету мне \U0001F3D6 "
        "\nБольше тебе не нужно самому проверять цены предметов, которые ты купил и "
        "потом искать за сколько и когда ты их купил, "
        "просто спроси у меня и я выдам тебе всю нужную информацию!"
        "\nВступайте в наш [новостной канал](https://t.me/tradematenews), все новости по боту, "
        "а также уведомления о технических работах будут именно там."
        "\U0001F911\n\nПеред началом работы, выбери свою валюту с помощью кнопок.",

    EN: "Welcome to TradeMateBot! \U0001F916"
        "\n\nThis bot is dedicated to help you with CS:GO investments "
        "\U0001F4B0\n\nWhat can I do? \U0001F3AF"
        "\n\n- I can remember all your deals, so you don't miss a thing "
        "\U0001F4DD\nFor example when you buy or sell something just let "
        "me know and I'll remember it\U0001F60E\U0001F4AD "
        "\n\n- I can track all prices and profits in real time for you, "
        "just relax and let me do the hard work \U0001F3D6 "
        "\nYou don't have to check skins' prices one by one and then "
        "find what did you buy them for, "
        "just ask me and you'll know everything you need to know\U0001F911"
        "\nJoin our [news channel](https://t.me/tradematenews), "
        "all bot related news and maintenance announcements will be made "
        "there.\nTo start using bot, set your currency using buttons below."
}

welcome_back = {
    RU: "Добро пожаловать обратно! \U0001F44B\n"
        "Наберите /menu, чтобы начать пользоваться ботом, или /help, если хотите узнать "
        "о его возможностях.",

    EN: "Welcome back! \U0001F44B\n"
        "Enter /menu to start or /help if you want to know more about bot's features."
}

help_message = {
    RU: "Перейдя по [ссылке](https://telegra.ph/TradeMate-Info-07-16) вы можете ознакомиться с "
        "инструкцией к боту. "
        "В случае, если у вас все еще остались вопросы по работе бота или "
        "есть предложения по дальнейшему развитию бота - напишите @rflktr\n\n"
        "/menu - переход в меню из любой точки диалога\n"
        "/setcurrency - изменить валюту\n"
        "/setlang - изменить язык\n\n"
        "\U000026A0 Чтобы начать пользовать ботом, нужно подписаться на наш "
        "[новостной канал](https://t.me/tradematenews). Все новости по боту, "
        "а также уведомления о тех. работах будут именно там.",

    EN: "Here's detailed [guide](https://telegra.ph/TradeMate-Info-07-16) to this bot. If you "
        "still have unanswered questions or wish to contact us, message @rflktr\n\n"
        "/menu - returns you to main menu from any point\n"
        "/setcurrency - changes your currency\n"
        "/setlang - changes your language\n\n"
        "/wipeout - deletes all deals and items\n\n"
        "\U000026A0 To start using bot you need to join our "
        "[news channel](https://t.me/tradematenews). "
        "All bot related news and maintenance announcements will be made there."
}

menu_message = {
    RU: "`Deals` -> для добавления новой сделки.\n`Notifications` -> настройка уведомлений по "
        "предметам.\n`Stats` -> раздел статистики.\n"
        "`Tracking` -> вызов таблицы с данными о ваших сделках (цены, "
        "прибыль и т.д.).\n\n"
        "Наберите /help, если хотите узнать больше о возможностях бота, или есть вопросы "
        "по его работе.",

    EN: "`Deals` -> use this button if you want to add a new deal.\n`Notifications` -> "
        "notifications settings for items.\n`Stats` -> show statistics.\n"
        "`Tracking` -> use this button if you want to see info about your added deals (prices, "
        "profits, hold days, etc.)\n\n"
        "Enter /help if you want to know more about bot's features or need help."
}

sort_key_message = {
    RU: "Выберите параметр прибыли для сортировки:\n`%` -> по процентам\n"
        "`Value` -> по абсолютной величине",

    EN: "Choose income sorting parameter:\n`%` -> by percent\n"
        "`Value` -> by absolute value"
}

sort_stats_key_message = {
    RU: "Выберите параметр для сортировки статистики:\n"
        "`Newest` -> по последним сделкам продажи\n"
        "`%` -> по процентам\n"
        "`Value` -> по абсолютной величине",

    EN: "Choose sorting parameter:\n"
        "`Newest` -> by last sell-deal\n"
        "`%` -> by percent\n"
        "`Value` -> by absolute value"
}

menu_unknown_message = {
    RU: "Выберите действие, нажав на одну из кнопок, если у вас возникли проблемы, "
        "наберите /help",

    EN: "Choose action by buttons below, if have any trouble use /help"
}

item_error_message = {
    RU: "По вашему запросу найдено слишком много предметов - `{length}`, пожалуйста, "
        "уточните запрос.",

    EN: "Too many items found - `{length}`, please refine your query."
}

deal_type_message = {
    RU: "Выберите тип сделки.",

    EN: "Select the deal item_type."
}

select_item_error_message = {
    RU: "Предмета с таким номером не нашлось, попробуйте еще раз.\n\nНаберите /menu, "
        "чтобы вернуться к меню, или /help, если нужна помощь.",

    EN: "There are no items matching this number.\nPlease try again.\n\nEnter /menu to reset "
        "current action and go to menu or /help if you want to know more about bot's features "
        "or need help."
}

select_item_skip_message = {
    RU: "Сперва найдите ваш предмет с помощью запроса.\n"
        "Наберите /help, если нужна помощь.",

    EN: "You need to query items first.\n"
        "Enter /help if you need help."
}

item_limit_reached_message = {
    RU: "Вы достигли ограничения на количество предметов - 96 шт.",

    EN: "You have reached items count limit of 96.",
}

item_not_set = {
    RU: "Похоже вы пропустили несколько шагов, сперва выберите предмет с помощью запроса.\n\n"
        "Если хотите прервать действие и вернуться меню, наберите /menu или /help, "
        "если возникли вопросы.",

    EN: "Looks like you've missed a few steps, first you need to find item using our "
        "query\n\nIf you want to reset current action and go to menu enter /menu or /help "
        "if you need help."
}

deal_type_not_set = {
    RU: "Вы не указали тип сделки. Пожалуйста, выбери тип сделки с помощью кнопки.",

    EN: "Deal item_type is not set. Please choose one by clicking button below."
}

item_count_negative = {
    RU: "Вы не можете купить `{count}` предметов.",

    EN: "You can not buy `{count}` items."
}

item_count_limit_reached = {
    RU: "Вы указали слишком больше количество предметов. Максимальное количество - "
        "99999, чтобы продолжить уменьшите значение.",

    EN: "You are trying to add too many items. Please decrease items count "
        "(maximum value is 99999)."
}

item_price_negative = {
    RU: "Ошибка, цена предмета может быть либо положительно либо 0 (напр. подарок)",

    EN: "Error, price can be only positive or 0 (gift)."
}

item_price_too_small = {
    RU: "Вы не можете продать/купить предмет за слишком маленькую цену. "
        "Минимальная цена - `0.01` (или 0, если это подарок)",

    EN: "You can not buy/sell items for too small value. Minimum value is `0.01`."
}

item_price_too_high = {
    RU: "Цена предмета не может превышать `{price_limit} {currency}`.",

    EN: "Item price can't be more than `{price_limit} {currency}`."
}

item_sell_for_zero = {
    RU: "Вы не можете продать предмет за 0 `{currency}`. "
        "Минимальная цена продажи - `0.01`",

    EN: "You can not sell item for 0 `{currency}`. Minimum value is `0.01`."
}

item_count_error = {
    RU: "Вы пытаетесь продать `{count}` `{item_name}`, но у вас добавлено "
        "только `{item_count}`.\n"
        "Пожалуйста, сократите количество или добавьте еще предметов через сделку покупки.",

    EN: "You are trying to sell `{count}` `{item_name}`, but you have only `{item_count}` "
        "in inventory.\n"
        "Please add more `buy`-deals with that item or decrease count in `sell`-deal."
}

deal_added_message = {
    RU: "`{deal_type}`-сделка с `{item_name}` добавлена.\n"
        "Количество предметов -> {count}\n"
        "Цена за штуку -> {price} {currency}",

    EN: "`{deal_type}`-deal with item `{item_name}` added.\n"
        "Number of item(s) -> {count}\n"
        "Price per item -> {price} {currency}"
}

unknown_query_message = {
    RU: "Неправильный запрос :(\n"
        "Вот еще несколько примеров правильных запросов:\n"
        "Field Tested M4A1-S Cyrex -> `w m4 cyrex ft`\n"
        "Стикер Zywoo с Берлина -> `s zywoo berlin`\n"
        "Хрома кейс -> `c chroma`\n"
        "Сувенирный набор Мираж с Катовице 2019 -> `c mirage katowice 2019` \n"
        "Теперь попробуйте еще раз\n\n"
        "Наберите /menu, чтобы отменить текущее действие и попасть в меню, или /help, "
        "если нужна помощь.",

    EN: "Your query is wrong :(\n"
        "Let me show you some more examples:\n"
        "Field Tested M4A1-S Cyrex -> `w m4 cyrex ft`\n"
        "Berlin Zywoo sticker -> `s zywoo berlin`\n"
        "Chroma case -> `c chroma`\n"
        "Mirage souvenir package from Katowice 2019? -> `c mirage katowice 2019` \n"
        "Now try again\n\n"
        "Enter /menu to reset current action and go to menu or /help if you need help."
}

query_message = {
    RU: "Чтобы добавить сделку, сначала найдите свой предмет с помощью запроса, примеры ниже:\n"
        "\U0001F52B оружия -> `w awp beast ft st` или `w glock fade fn`\n"
        "\U0001F52A ножи -> `k talon fade fn st`\n"
        "\U0001F5BC стикеры -> `s howl` или `s zywoo`\n"
        "\U0001F9E7 патчи -> `p bravo`\n"
        "\U0001F46E агенты -> `a ct ava`\n"
        "\U0001F9F0 контейнеры -> `c chroma` или `c berlin autograph` \n"
        "\U0001F6E0 расходники -> `t phoenix key` или `t berlin pass`\n"
        "\U0001F9E4 перчатки -> `g hand wraps fn` или `g vice mw`\n"
        "Наберите /menu, чтобы отменить текущее действие и попасть в меню, или /help, "
        "если нужна помощь.",

    EN: "To add a deal you need to find your item with our query using examples below:\n"
        "\U0001F52B weapon -> `w awp beast ft st` or `w glock fade fn`\n"
        "\U0001F52A knife -> `k talon fade fn st`\n"
        "\U0001F5BC sticker -> `s howl` or `s zywoo`\n"
        "\U0001F9E7 patch -> `p bravo`\n"
        "\U0001F46E agents-> `a ct ava` \n"
        "\U0001F9F0 container -> `c chroma` or `c berlin autograph` \n"
        "\U0001F6E0 tool -> `t phoenix key` or `t berlin pass`\n"
        "\U0001F9E4 gloves -> `g hand wraps fn` or `g vice mw`\n"
        "Enter /menu to reset current action and go to menu or /help if you need help."
}

item_price_not_set = {
    RU: "Вы пытаетесь добавить сделку продажи с "
        "`{item_name}`, но вы не указали, что покупали этот предмет. Сперва добавьте его "
        "через сделку покупки. Если это был подарок, то можете добавить с ценой 0.",

    EN: "You are trying to add `sell`-deal with "
        "'`{item_name}`' but i don't know anything about the "
        "price at which you bought it. First of all you need to add "
        "`buy`-deal with that item. If it was a gift or you got it "
        "for free, add a deal with price equals to 0."
}

wrong_currency_message = {
    RU: "Вы пытаетесь добавить сделку продажи с {currency} для предмета `{item_name}`, "
        "но вы купили его за `{comma_currencies}`. Если вы хотите добавить эту сделку продажи, то, "
        "пожалуйста, поменяйте валюту на `{or_currencies}`, используя команду /setcurrency.",

    EN: "You are trying to add a `sell`-deal "
        "using currency `{currency}` for "
        "{item_name}, but you used `{comma_currencies}` "
        "to purchase it. If you want to add this `sell`-deal "
        "please change your currency to "
        "`{or_currencies}` using /setcurrency command.",
}

item_price_count_stage = {
    RU: "Вы добавляете `{deal_type}`-сделку с `{item_name}`.\n"
        "Отправьте две цифры, например, `2 100`, где `2` - это количество, а `100` - цена за штуку",

    EN: "You are going to add `{deal_type}`-deal with `{item_name}`.\n"
        "Simply send me two numbers, for example `2 100`, where `2` is number of items and `100` "
        "is price per item."
}

tracking_is_empty = {
    RU: "У вас нет предметов, по которым можно было бы посмотреть информацию. Добавьте их через "
        "/menu -> Deals",

    EN: "You don't have any items to show. You can add them in /menu -> Deals"
}

stats_is_empty = {
    RU: "У вас нет сделок продажи с предметами, чтобы отобразить статистику. Добавьте их через "
        "/menu -> Deals",

    EN: "You don't have any `sell`-deals to show stats. You can add them in /menu -> Deals"
}

tracking_generation_message = {
    RU: "Генерируем таблицу...\n"
        "Текущие цены взяты из Торговой Площадки Steam (иногда он возвращает неверные цены) и "
        "обновляются каждые полчаса.\nКомиссия Steam (13%) уже учтена в расчете Income.",

    EN: "Image generation in progress...\n"
        "Current prices are taken from Steam Market (sometimes steam returns wrong prices), and "
        "updated every 30 minutes. \nSteam fee (13%) is already included in profit count."
}

stats_generation_message = {
    RU: "Рассчитываем статистику...\n",

    EN: "Stats calculation in progress...\n"
}

item_found_picker = {
    RU: "Напиши номер нужного предмета (один за раз).\n",

    EN: "Send me your item's number (only one at time).\n"
}

item_not_exist = {
    RU: "Предмета по вашему запросу \n`{text}`\n не существует. "
        "Проверьте правильность запроса.",

    EN: "Sorry, but i could not find any item with your request\n`{text}`"
        "\nPlease specify your query."
}

subscriber_message = {
    RU: "\U000026D4 Подпишишь на наш [новостной канал](https://t.me/tradematenews), "
        "чтобы начать пользоваться ботом.",

    EN: "\U000026D4 Join our [news channel](https://t.me/tradematenews) "
        "to start using bot."
}

no_items = {
    RU: "У вас нет предметов для выбора. Добавьте их через сделку покупки в /menu -> Deals.",

    EN: "You don't have any items to choose. You can add them in /menu -> Deals."
}

page = {
    RU: "Страница",

    EN: "Page"
}

notify_type_choose = {
    RU: "Выберите тип уведомления.",

    EN: "Choose notification item_type."
}

notify_item_choose = {
    RU: 'Вы выбрали `{item_name}`. Напишите цену в `{currency}`, при достижении которой '
        'вы хотите получить уведомление. Средняя цена покупки этого предмета равна '
        '`{avg_price} {currency}`.',

    EN: 'You choose `{ite_name}`. Now send price in `{currency}` for notification. '
        'Average buy price of that item is `{avg_price} {currency}`.'
}

notify_item_not_choose = {
    RU: "Вы не выбрали предмет. Выберите его, нажав на соотвествующий номер.",

    EN: "You didn't choose an item. Pick it by clicking corresponding number."
}

notify_take_profit_invalid = {
    RU: "Цена для фиксации прибыли не должна быть меньше или равна средней цене покупки предмета.",

    EN: "Take-profit price can not be less than or equal to average buy price of item."
}

notify_take_profit_set = {
    RU: 'Для предмета `{item_name}` установлен порог фиксации прибыли, равный `{price} '
        '{currency}`. При достижении этого порога вы получите уведомление.',

    EN: 'Take-profit price is set to `{price} {currency}` for the item `{item_name}`. '
        'You will receive notification when price will reach that value.'
}

notify_take_profit_reached = {
    RU: "По этим предметам произошло превышение порога, установленного на цену "
        "(пороговая цена -> цена сейчас):\n",

    EN: "This item's take-profit price is reached (take profit price -> current price):\n"
}

stop_loss_not_implemented = {
    RU: "Функционал уведомлений по потерям ешё не реализован.",

    EN: "Stop loss notifications not implemented yet."
}

wipeout_message = {
    RU: "Вы уверены, что хотите удалить все предметы и сделки с ними?",

    EN: "Are you sure you want to delete all items and deals with them?"
}

wipeout_yes = {
    RU: "Точно уверены?",

    EN: "Really sure?"
}

wipeout_no = {
    RU: "Наберите /menu чтобы продолжить.",

    EN: "Enter /menu to continue."
}

wipeout_sure = {
    RU: "Все ваши предметы и сделки удалены.\n\nНаберите /menu чтобы продолжить.",

    EN: "All your items and deals have been deleted.\n\nEnter /menu to continue."
}

wipeout_no_items = {
    RU: "У вас нет предметов и сделок для удаления.\n\nНаберите /menu чтобы продолжить.",

    EN: "You don't have any items and deals for deleting.\n\nEnter /menu to continue."
}

cannot_change_currency = {
    RU: "Вы пока не можете изменить валюту. Изменение валюты с автоматическим пересчётом сделок "
        "будет добавлено позднее.\n\nНапишите @rflktr, если действительно хотите изменить валюту."
        "\n\nНаберите /menu чтобы продолжить.",

    EN: "You can not change currency yet. Changing currency with automatic deals recalculation "
        "will be implemented later.Contact @rflktr if you really want to change currency."
        "\n\nEnter /menu to continue."
}
