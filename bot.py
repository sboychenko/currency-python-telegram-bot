import datetime
import requests
import logging
import pytz
from telegram.ext import Updater, CommandHandler
from bs4 import BeautifulSoup

BOT_TOKEN = "token"
CHAT_ID = "123"

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/56.0.2924.87 Safari/537.36',
}
MIR_URL = "https://mironline.ru/support/list/kursy_mir/"
BNB_URL = "https://bnb.by/kursy-valyut/imbank/"


def get_mir_currency_info():
    # Request the website HTML content
    response = requests.get(MIR_URL, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table with the currency information
    table = soup.find("div", {"class": "sf-text"}).find("table")

    # Extract the currency information
    currencies = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 2:
            currency = cells[0].text.strip()
            rate = cells[1].text.strip()
            currencies.append((currency, rate))

    return currencies


def get_bnb_currency_info():
    # Request the website HTML content
    response = requests.get(BNB_URL, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table with the currency information
    table = soup.find("div", {"class": "currency_wrap_ibank"}).find("table")

    # Extract the currency information
    currencies = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 3:
            currency = cells[0].text.strip()
            rate = cells[2].text.strip()
            currencies.append((currency, rate))

    return currencies


def find_exchange_rate(currencies):
    return float(currencies[0][1].replace(",", "."))


def build_currency_info(currencies, exchange_rate):
    message = f"Date: {datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')).strftime('%d/%m/%Y %H:%M')}\n\n"
    for currency, rate in currencies:
        message += f"{currency}: {rate}\n"

    if exchange_rate is not None:
        message += f"\nExchange rate (RUB to USD): {exchange_rate:.2f}\n"

    return message


def command_help(update, context):
    message = 'Welcome to the MIR-BNB currency bot'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def command_solve_currency(update, context):
    solve_currency(context, update.effective_chat.id)


def job_solve_currency(context):
    solve_currency(context, CHAT_ID)


def solve_currency(context, chat_id):
    mir_currencies = get_mir_currency_info()
    mir = [row for row in mir_currencies if 'Белорусский рубль' == row[0]]
    print(mir_currencies)

    bnb_currencies = get_bnb_currency_info()
    bnb = [row for row in bnb_currencies if 'USD' == row[0]]
    print(bnb_currencies)

    exchange_rate = find_exchange_rate(mir) * find_exchange_rate(bnb)

    message = build_currency_info(mir + bnb, exchange_rate)
    context.bot.send_message(chat_id=chat_id, text=message)


# Bot for send currency to CHAT_ID
if __name__ == "__main__":
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    j = updater.job_queue

    start_handler = CommandHandler('start', command_help)
    dispatcher.add_handler(start_handler)
    help_handler = CommandHandler('help', command_help)
    dispatcher.add_handler(help_handler)

    currency_handler = CommandHandler("now", command_solve_currency)
    dispatcher.add_handler(currency_handler)

    updater.start_polling()

    job_daily = j.run_daily(
        job_solve_currency,
        days=(0, 1, 2, 3, 4, 5, 6),
        time=datetime.time(hour=10, minute=00, second=00, tzinfo=pytz.timezone("Europe/Moscow"))
    )
