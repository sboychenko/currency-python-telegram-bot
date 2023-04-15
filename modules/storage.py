from datetime import timedelta

import modules


class CurrencyInfo:
    def __init__(self, date, byn_mir, usd_bnb, usd_bnb_mir, usd_cbr):
        self.date = date
        self.byn_mir = byn_mir
        self.usd_bnb = usd_bnb
        self.usd_bnb_mir = usd_bnb_mir
        self.usd_cbr = usd_cbr


def save_to_redis(redis, ci):
    d = ci.date.strftime('%Y-%m-%d-%H-%M')
    eleven_days = 60 * 60 * 24 * 11
    redis.set(f'rate:{modules.parsers.BYN}-MIR:{d}', ci.byn_mir, ex=eleven_days)
    redis.set(f'rate:{modules.parsers.USD}-BNB:{d}', ci.usd_bnb, ex=eleven_days)
    redis.set(f'rate:{modules.parsers.USD}-MIR:{d}', ci.usd_bnb_mir, ex=eleven_days)
    redis.set(f'rate:{modules.parsers.USD}-CBR:{d}', ci.usd_cbr, ex=eleven_days)


def get_last_currency(redis, date):
    yesterday = date - timedelta(days=1)
    pattern = yesterday.strftime('%Y-%m-%d')

    data = []
    for key in redis.scan_iter(f"rate:*:{pattern}*"):
        data.append((key, redis.get(key)))

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


def get_all(redis):
    data = []
    for key in redis.scan_iter("*"):
        data.append((key, redis.get(key)))
    return data


def clear():
    r.flushall()
    r.flushdb()
    for key in r.scan_iter("*"):
        r.delete(key)
