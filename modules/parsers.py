import pytz
import requests
import xml.etree.ElementTree as et
from bs4 import BeautifulSoup
from datetime import datetime

from modules.storage import CurrencyInfo

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/56.0.2924.87 Safari/537.36',
}

MIR_URL = "https://mironline.ru/support/list/kursy_mir/"
BNB_URL = "https://bnb.by/kursy-valyut/imbank/"
CBR_URL = 'https://www.cbr.ru/scripts/XML_daily.asp'

USD = 'USD'
BYN = 'BYN'
RUB = 'RUB'


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


# Код для получения курса валюты с помощью API Центрального Банка России
def get_cbr_currency_info():
    # Отправка запроса к API
    response = requests.get(CBR_URL)

    # Обработка ответа
    root = et.fromstring(response.content)
    currencies = []
    for valute in root.findall('.//Valute'):
        currencies.append((valute.find('CharCode').text, valute.find('Value').text))

    return currencies


def get_rate(currencies, code):
    find = [row for row in currencies if code == row[0]]
    print(currencies)
    return float(find[0][1].replace(",", "."))


def solve_currency():
    date = datetime.now(tz=pytz.timezone('Europe/Moscow'))

    mir_currencies = get_mir_currency_info()
    byn_mir = get_rate(mir_currencies, 'Белорусский рубль')

    bnb_currencies = get_bnb_currency_info()
    usd_bnb = get_rate(bnb_currencies, USD)

    usd_bnb_mir = byn_mir * usd_bnb

    cbr_currencies = get_cbr_currency_info()
    usd_cbr = get_rate(cbr_currencies, USD)

    return CurrencyInfo(date, byn_mir, usd_bnb, usd_bnb_mir, usd_cbr)
