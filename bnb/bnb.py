import ccxt
import time
import pandas as pd
import math
from datetime import datetime

# --- 基础配置 ---
API_KEY = '5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'
API_SECRET = 'DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'

SYMBOL = 'BNB/USDT'
BUY_AMOUNT_USDT = 50  # 每次买入 50 USDT

# --- 衰减逻辑参数 (10分钟从2%降至0.4%) ---
INITIAL_TP = 0.02  # 初始目标 2%
MIN_TP = 0.004  # 最低保底 0.4%
DECAY_CONSTANT = 0.3  # 分钟级衰减系数 (0.3 约在 10-12 分钟趋于平缓)

# 初始化交易所
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})
# 测试环境开关 (实盘请设为 False)
exchange.set_sandbox_mode(True)


def fetch_rsi(symbol, period=14):
    try:
        # 获取 5 分钟 K 线
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        return rsi
    except Exception as e:
        print(f"\n⚠️ 获取 RSI 失败: {e}")
        return 50


def get_dynamic_tp(buy_time):
    """
    根据买入时间计算当前动态止盈率
    公式: (初始-最低) * e^(-k * 分钟) + 最低
    """
    minutes_held = (datetime.now() - buy_time).total_seconds() / 60
    current_tp = (INITIAL_TP - MIN_TP) * math.exp(-DECAY_CONSTANT * minutes_held) + MIN_TP
    return current_tp


def main():
    in_position = False
    buy_price = 0
    buy_time = None
    amount = 0

    print(f"🚀 策略启动 | 交易对: {SYMBOL}")
    print(f"📈 初始止盈: {INITIAL_TP:.2%} | 保底止盈: {MIN_TP:.2%} | 衰减节奏: 10分钟")
    print("-" * 50)

    while True:
        try:
            # 1. 获取当前市场价格 (取卖一价作为参考)
            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']

            if not in_position:
                rsi = fetch_rsi(SYMBOL)
                print(f"🔍 扫描中 | RSI: {rsi:.2f} | 价格: {current_price}", end='\r')

                # 买入触发条件：RSI 低于 35
                if rsi < 35:
                    print(f"\n📉 信号触发！RSI {rsi:.2f} < 35，执行买入...")

                    # 计算下单数量并符合交易所精度要求
                    raw_amount = BUY_AMOUNT_USDT / current_price
                    amount = float(exchange.amount_to_precision(SYMBOL, raw_amount))

                    # 执行市价买单
                    order = exchange.create_market_buy_order(SYMBOL, amount)

                    # 记录买入信息 (优先取成交均价)
                    buy_price = order.get('average', order.get('price', current_price))
                    buy_time = datetime.now()
                    in_position = True

                    print(f"✅ 已成交！买入价: {buy_price} | 数量: {amount} | 时间: {buy_time.strftime('%H:%M:%S')}")

            else:
                # 2. 持仓中，计算动态目标价
                tp_rate = get_dynamic_tp(buy_time)
                target_price = buy_price * (1 + tp_rate)

                elapsed_min = (datetime.now() - buy_time).total_seconds() / 60

                print(
                    f"⏳ 持仓 {elapsed_min:.1f}min | 实时止盈位: {tp_rate:.2%} | 目标价: {target_price:.2f} | 当前价: {current_price}",
                    end='\r')

                # 卖出触发条件：当前价超过动态目标价
                if current_price >= target_price:
                    print(f"\n💰 达到目标！当前价 {current_price} >= 目标价 {target_price:.2f}")

                    # 执行市价卖单 (全平)
                    exchange.create_market_sell_order(SYMBOL, amount)

                    in_position = False
                    profit = (current_price - buy_price) / buy_price
                    print(f"💵 卖出离场 | 结算盈利: {profit:.2%} | 持仓时长: {elapsed_min:.1f} 分钟")
                    print("-" * 50)

            # 轮询频率 (1-3秒一次)
            time.sleep(1)

        except Exception as e:
            print(f"\n❌ 运行异常: {str(e)}")
            time.sleep(1)  # 报错后稍作等待防止刷屏


if __name__ == "__main__":
    main()