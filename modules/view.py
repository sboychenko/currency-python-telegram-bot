import io
import logging

from matplotlib import pyplot as plt


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
