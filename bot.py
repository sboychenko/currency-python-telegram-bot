import logging
import os
import pytz
import redis
from datetime import time
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler
from modules import storage, parsers, view

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PASS = os.getenv('REDIS_PASS')


def command_help(update, context):
    logging.info("Help command")
    message = 'Welcome to the MIR-BNB currency bot'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)


def command_solve_currency(update, context):
    logging.info("Now command")
    ci = parsers.solve_currency()
    message = view.build_currency_info(ci)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)


def job_solve_currency(context):
    logging.info("Start currency job")
    ci = parsers.solve_currency()
    storage.save_to_redis(r, ci)
    last_ci = storage.get_last_currency(ci.date)

    img = view.build_graph()
    text = view.build_currency_info(ci, last_ci)
    context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=img, caption=text, parse_mode=ParseMode.MARKDOWN)


def get_all_redis(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=storage.get_all(r), parse_mode=ParseMode.MARKDOWN)


def test(update, context):
    # job_solve_currency(context)
    context.bot.send_message(chat_id=update.effective_chat.id, text="done", parse_mode=ParseMode.MARKDOWN)


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

    get_all_redis_handler = CommandHandler("get_all", get_all_redis)
    dispatcher.add_handler(get_all_redis_handler)

    updater.start_polling()

    # todo поменять на запуск раз в Т часов или CRON
    job_daily = j.run_daily(
        job_solve_currency,
        days=(0, 1, 2, 3, 4, 5, 6),
        time=time(hour=10, minute=00, second=00, tzinfo=pytz.timezone("Europe/Moscow"))
    )
