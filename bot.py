import logging
import math
import os
import matplotlib.pyplot as plt
import pytz
import redis
import io
from datetime import datetime, time, timedelta
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler

import modules.parsers

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PASS = os.getenv('REDIS_PASS')


class CurrencyInfo:
    def __init__(self, date, byn_mir, usd_bnb, usd_bnb_mir, usd_cbr):
        self.date = date
        self.byn_mir = byn_mir
        self.usd_bnb = usd_bnb
        self.usd_bnb_mir = usd_bnb_mir
        self.usd_cbr = usd_cbr


def command_help(update, context):
    logging.info("Help command")
    message = 'Welcome to the MIR-BNB currency bot'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)


def command_solve_currency(update, context):
    logging.info("Now command")
    ci = solve_currency()
    message = build_currency_info(ci)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)


def job_solve_currency(context):
    logging.info("Start currency job")
    ci = solve_currency()
    save_to_redis(ci)
    last_ci = get_last_currency(ci.date)

    img = build_graph()
    text = build_currency_info(ci, last_ci)
    context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=img, caption=text, parse_mode=ParseMode.MARKDOWN)


def save_to_redis(ci):
    d = ci.date.strftime('%Y-%m-%d-%H-%M')

    r.set(f'rate:{modules.parsers.BYN}-MIR:{d}', ci.byn_mir, ex=15_000)
    r.set(f'rate:{modules.parsers.USD}-BNB:{d}', ci.usd_bnb, ex=15_000)
    r.set(f'rate:{modules.parsers.USD}-MIR:{d}', ci.usd_bnb_mir, ex=15_000)
    r.set(f'rate:{modules.parsers.USD}-CBR:{d}', ci.usd_cbr, ex=15_000)


def get_last_currency(date):
    yesterday = date - timedelta(days=1)
    pattern = yesterday.strftime('%Y-%m-%d')

    data = []
    for key in r.scan_iter(f"rate:*:{pattern}*"):
        data.append((key, r.get(key)))

    ci = CurrencyInfo(yesterday, None, None, None, None)
    for key, value in data:
        value = float(value)
        if "USD-MIR" in key:
            ci.usd_bnb_mir = value
        if "BYN-MIR" in key:
            ci.byn_mir = value
        if "USD-BNB" in key:
            ci.usd_bnb = value
        if "USD-CBR" in key:
            ci.usd_cbr = value
    return ci


def solve_currency():
    date = datetime.now(tz=pytz.timezone('Europe/Moscow'))

    mir_currencies = modules.parsers.get_mir_currency_info()
    byn_mir = modules.parsers.get_rate(mir_currencies, 'Белорусский рубль')

    bnb_currencies = modules.parsers.get_bnb_currency_info()
    usd_bnb = modules.parsers.get_rate(bnb_currencies, modules.parsers.USD)

    usd_bnb_mir = byn_mir * usd_bnb

    cbr_currencies = modules.parsers.get_cbr_currency_info()
    usd_cbr = modules.parsers.get_rate(cbr_currencies, modules.parsers.USD)

    return CurrencyInfo(date, byn_mir, usd_bnb, usd_bnb_mir, usd_cbr)


def build_currency_info(ci, last_ci=None):
    message = f"*\U0001F4B5: {ci.usd_bnb_mir:.2f}* | Δ{(ci.usd_bnb_mir - ci.usd_cbr):.2f}"
    if last_ci and last_ci.usd_bnb_mir:
        delta = ci.usd_bnb_mir - last_ci.usd_bnb_mir
        add = create_info(delta)
        message += f" | {add[0]} {add[1]}"
    message += "\n\n"

    delta = ci.usd_cbr - last_ci.usd_cbr if last_ci and last_ci.usd_cbr else None
    add = create_info(delta)
    message += f"\tCBR: {ci.usd_cbr:.2f} | {add[1]}\n"

    delta = ci.usd_bnb - last_ci.usd_bnb if last_ci and last_ci.usd_bnb else None
    add = create_info(delta)
    message += f"\tBNB: {ci.usd_bnb:.2f} | {add[1]}\n"

    delta = ci.byn_mir - last_ci.byn_mir if last_ci and last_ci.byn_mir else None
    add = create_info(delta)
    message += f"\tMIR: {ci.byn_mir:.2f} | {add[1]}\n"

    message += f"\n\U0001F4C6 {ci.date.strftime('%d/%m/%Y %H:%M')}\n\n"

    return message


def create_info(delta):
    sign = "\U00002B1C"
    info = ""
    if delta:
        sign = "\U00002B1C" if delta == 0 else "\U0001F4C9" if math.copysign(1, delta) == -1 else "\U0001F4C8"
        info = f"_{delta:.2f}_"
    return sign, info


def build_graph():
    data = []
    for key in r.scan_iter("rate:*"):
        data.append((key, r.get(key)))

    result = {}
    for row in data:
        elements = row[0].split(':')
        rate = float(row[1])
        date = elements[2].rsplit('-', 2)[0]
        if elements[1] not in result:
            result[elements[1]] = []
        result[elements[1]].append((rate, date))

    logging.debug("Data for graph: ", result)

    fig, ax = plt.subplots(2, sharex=True)
    fig.suptitle('USD rate for the last 10 days')

    for rates in result:
        print(rates)
        print(result.get(rates))
        cur_rate = []
        dates = []
        for rate in result.get(rates):
            cur_rate.append(rate[0])
            dates.append(rate[1])
        i = 0 if ['USD-CBR', 'USD-MIR'].__contains__(rates) else 1
        ax[i].plot(dates, cur_rate, label=rates)  # color="tab:orange",
        ax[i].legend(loc='lower right')

    plt.xlabel('Date')
    plt.ylabel('Rate')
    # plt.show()

    # save plot as png
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return img


def test(update, context):
    # job_solve_currency(context)

    date = datetime.now()
    ci = get_last_currency(date + timedelta(days=1))
    last_ci = get_last_currency(ci.date)

    text = build_currency_info(ci, last_ci)
    img = build_graph()
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text, parse_mode=ParseMode.MARKDOWN)
    # context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN)


# Bot for send currency to CHAT_ID
if __name__ == "__main__":
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    j = updater.job_queue
    r = redis.StrictRedis(host=REDIS_HOST, password=REDIS_PASS, port=6379, db=0,
                          charset="utf-8", decode_responses=True)

    start_handler = CommandHandler('start', command_help)
    dispatcher.add_handler(start_handler)
    help_handler = CommandHandler('help', command_help)
    dispatcher.add_handler(help_handler)

    currency_handler = CommandHandler("now", command_solve_currency)
    dispatcher.add_handler(currency_handler)

    test_handler = CommandHandler("test", test)
    dispatcher.add_handler(test_handler)

    updater.start_polling()

    # todo поменять на запуск раз в Т часов или CRON
    job_daily = j.run_daily(
        job_solve_currency,
        days=(0, 1, 2, 3, 4, 5, 6),
        time=time(hour=10, minute=00, second=00, tzinfo=pytz.timezone("Europe/Moscow"))
    )
