from dataclasses import dataclass
from typing import Optional


@dataclass
class Date:
    year: int
    month: int
    day: int


@dataclass
class Record_Price:
    price: float
    time: Date


@dataclass
class Holding:
    name: str #当前持仓标的名称
    amount: int #当前持仓股数
    cost: float #当前持仓单股成本价
    current_price: float #当前持仓单股价格。
    current_value: float #当前持仓总价值。current_value=current_price*amount
    current_profit: float #当前持仓总收益。current_profit=(current_price-cost_price)*amount
    current_yield: float #当前持仓收益率。current_yield=100*(current_price/cost_price-1)。例如持仓成本价格为100美元，当前价格为120美元，则该持仓current_yield值为20.00
    percentage: float #该持仓占总投资资金量的比例。例如持仓价值5000美元，账户总资产价值10000美元，则该持仓percentage值为50.00


@dataclass
class Account:
    total_capital: float
    available_capital: float
    holding: Holding
    have_holding: bool


def break_previous_cycle_peak(previous_cycle_peak, current_price):
    if current_price > previous_cycle_peak.price:
        return True
    else:
        return False


def drop_3_percent_in_one_day(yesterday_close, current_price):
    if current_price < 0.97 * yesterday_close:
        return True
    else:
        return False


def drop_6_percent_in_total(all_time_high, current_price):
    if current_price < 0.94 * all_time_high.price:
        return True
    else:
        return False


def get_current_price():
    # 后续需要接入券商API实时返回当前价格
    # 需要加入获取失败的容错机制
    current_price = float(input("请输入当前价格"))
    return current_price


def market_open():
    # 后续要接入券商API获取开盘信号
    open_signal = int(input("是否开盘？（1：开盘，0：未开盘）"))
    while open_signal not in (0, 1):
        open_signal = int(input("输入无效！\n" + "是否开盘？（1：开盘，0：未开盘）"))
    if open_signal == 0:
        print("未开盘")
        return False
    elif open_signal == 1:
        print("已开盘")
        return True


def market_opening(signal_price):
    # 目前以获取到signal_price为-1为收盘信号
    if signal_price != -1:
        return True
    else:
        return False


def market_closing(open_signal):
    if open_signal == False:
        return True
    else:
        return False


def market_close(today, current_price, open_signal, yesterday_close):
    today = date_pass(today)
    open_signal = False
    yesterday_close = current_price
    return today, current_price, open_signal, yesterday_close


def open_position(account, current_price):
    account.holding = Holding(
        "黄金ETF（IAU）",
        int(account.available_capital / current_price),
        current_price,
        current_price,
        current_price * int(account.available_capital / current_price),
        0.00,
        0.00,
        100 * current_price * int(account.available_capital / current_price) / account.total_capital
    )
    account.have_holding = True
    account.available_capital -= account.holding.current_value
    print(
        "开始做多。" +
        "\n标的名称：" + str(account.holding.name) +
        "\n当前成本：" + str(account.holding.cost) +
        "\n当前股数：" + str(account.holding.amount) +
        "\n当前价格：" + str(account.holding.current_price) +
        "\n持仓价值：" + str("{:.2f}".format(account.holding.current_value)) +
        "\n当前利润：" + str("{:.2f}".format(account.holding.current_profit)) +
        "\n当前收益率：" + str(account.holding.current_yield)[:5] + "%" +
        "\n持仓占比：" + str(account.holding.percentage)[:5] + "%"
    )
    return account


def sell(account, previous_cycle_peak, cycle_peak):
    account.available_capital = account.available_capital + float(account.holding.current_value)    # 释放可用资金
    account.holding = reset_position()                                                                             # 清空仓位
    account.have_holding = False
    previous_cycle_peak.price = cycle_peak.price                                                            # 周期新高变周期前高
    previous_cycle_peak.time = cycle_peak.time
    return account, previous_cycle_peak, cycle_peak


def reset_position():
    holding = Holding("", 0, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00)
    return holding


def update_holding(account, current_price):                                                                 # 按最新价格更新持仓信息
    account.holding.current_price = current_price
    account.holding.current_value = account.holding.amount * account.holding.current_price
    account.holding.current_profit = (account.holding.current_price - account.holding.cost) * account.holding.amount
    account.holding.current_yield = 100 * (account.holding.current_price / account.holding.cost - 1)
    account.total_capital = account.available_capital + account.holding.current_value
    account.holding.percentage = 100 * account.holding.current_value / account.total_capital
    return account, current_price


def print_account_info(account):
    if account.have_holding:
        print(
            "账户资产：" + str("{:.2f}".format(account.total_capital)) +
            "\n可用资金：" + str("{:.2f}".format(account.available_capital)) +
            "\n-------------【持仓信息】--------------" +
            "\n标的名称：" + str(account.holding.name) +
            "\n当前成本：" + str(account.holding.cost) +
            "\n当前股数：" + str(account.holding.amount) +
            "\n当前价格：" + str(account.holding.current_price) +
            "\n持仓价值：" + str("{:.2f}".format(account.holding.current_value)) +
            "\n当前利润：" + str("{:.2f}".format(account.holding.current_profit)) +
            "\n当前收益率：" + str(account.holding.current_yield)[:5] + "%" +
            "\n持仓占比：" + str(account.holding.percentage)[:5] + "%"
        )
    else:
        print(
            "账户资产：" + str("{:.2f}".format(account.total_capital)) +
            "\n可用资金：" + str("{:.2f}".format(account.available_capital)) +
            "\n-------------【持仓信息】--------------" +
            "\n暂无持仓"
        )


def date_pass(today):
    if today.day == 28 and today.month == 2:
        today.month += 1
        today.day = 1
    elif today.day == 30 and today.month in (4, 6, 9, 11):
        today.month += 1
        today.day = 1
    elif today.day == 31 and today.month in (1, 3, 5, 7, 8, 10, 12):
        today.month += 1
        today.day = 1
        if today.month == 13:
            today.month = 1
            today.year += 1
    else:
        today.day += 1
    return today


if __name__ == "__main__":
    account = Account(                                                                                                   # 初始化账户
        total_capital=1_000_000,
        available_capital=1_000_000,
        holding=reset_position(),
        have_holding=False
    )
                                                                                                                                  # 初始化策略配置参数
    previous_cycle_peak = Record_Price(39.36, Date(2022, 3, 8))                                 # 策略启动时，人为设定的周期前高和新高
    cycle_peak = Record_Price(39.36, Date(2022, 3, 8))
                                                                                                                                  # 初始化股市信息
    yesterday_close = previous_cycle_peak.price
    current_price = previous_cycle_peak.price
    signal_price = previous_cycle_peak.price
    today = Date(2022, 3, 8)
    open_signal = False

    while True:                                                                                                           # 每日重复
        while market_closing(open_signal):                                                                    # 未开盘则持续获取开盘信号。
            open_signal = market_open()
        while market_opening(signal_price):                                                                  # 获取到开盘信号进入循环：获取价格-判断价格是否触发建仓/清仓-观望/执行操作
            signal_price = get_current_price()

            if signal_price != -1:                                                                                      # 获取到信号价格为-1表示收盘，否则是实时价格
                current_price = signal_price
                if current_price > cycle_peak.price:                                                          # 价格破新高先记录，用于判断清仓条件
                    cycle_peak.price = current_price
                    cycle_peak.time = today
            else:
                signal_price = yesterday_close
                break

            if not account.have_holding:
                if break_previous_cycle_peak(previous_cycle_peak, current_price):         # 突破周期前高则买入
                    account = open_position(account, current_price)
                else:
                    print_account_info(account)                                                                # 否则观望
                    print("观望中......")
            else:
                account, current_price = update_holding(account, current_price)
                if drop_3_percent_in_one_day(yesterday_close, current_price):            # 单日跌幅超3%则清仓
                    account, previous_cycle_peak, cycle_peak = sell(account, previous_cycle_peak, cycle_peak)
                    print("由于单日跌幅超过3%，已清仓")
                elif drop_6_percent_in_total(cycle_peak, current_price):                       # 相较周期新高累计跌幅超过6%则清仓
                    account, previous_cycle_peak, cycle_peak = sell(account, previous_cycle_peak, cycle_peak)
                    print("由于相较新高累计跌幅超过6%，已清仓")
                else:
                    print_account_info(account)
                    print("持仓中......")

        today, current_price, open_signal, yesterday_close = market_close(today, current_price, open_signal, yesterday_close)
        print("已收盘，今日收盘价为" + str(current_price))
