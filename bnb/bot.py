import ccxt
import time
import pandas as pd
from datetime import datetime

# --- 基础配置 ---
API_KEY = '5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'
API_SECRET = 'DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'

API_KEY = 'rQjfBXYpVIpDbnaeSJfe7YG10w8FoHSYuo79TMwfTcuTGaLe3liqr4XnfFzdAaW0'
API_SECRET = 'T54p32JFeaItwlkJOWA6KDyIqiEa0a70AM8FLyTK8TQnj0hxEOy5ZmFyfT23uAI6'

SYMBOL = 'BTC/USDT'
BUY_AMOUNT_USDT = 50  # 每次下单金额
INITIAL_TP = 0.02  # 初始 2% 止盈
MIN_TP = 0.0035  # 覆盖手续费的保底收益 (0.35%)
DECAY_FACTOR = 0.15  # 衰减系数，越大降速越快

# 初始化币安测试网
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})
exchange.set_sandbox_mode(True)


def fetch_rsi(symbol, period=14):
    """获取RSI指标判断低点"""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
    delta = df['c'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]


def get_dynamic_tp(buy_time):
    """指数衰减计算止盈目标"""
    hours_held = (datetime.now() - buy_time).total_seconds() / 3600
    # 公式：P = (Pmax - Pmin) * e^(-k*t) + Pmin
    import math
    current_tp = (INITIAL_TP - MIN_TP) * math.exp(-DECAY_FACTOR * hours_held) + MIN_TP
    return current_tp


def main():
    in_position = False
    buy_price = 0
    buy_time = None
    amount = 0

    print(f"开始运行... 交易对: {SYMBOL}")

    while True:
        try:
            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']

            if not in_position:
                # 低点判断逻辑：RSI < 35 (超卖区)
                rsi = fetch_rsi(SYMBOL)
                print(f"🔍 扫描中 | RSI: {rsi:.2f} | 价格: {current_price}", end='\r')

                if rsi < 35:
                    print(f"\n📉 触发买入信号！RSI: {rsi:.2f}")
                    amount = BUY_AMOUNT_USDT / current_price
                    # order = exchange.create_market_buy_order(SYMBOL, amount) # 实盘/测试网下单
                    buy_price = current_price
                    buy_time = datetime.now()
                    in_position = True
                    print(f"✅ 已买入 | 均价: {buy_price}")

            else:
                # 动态计算当前需要的涨幅
                tp_rate = get_dynamic_tp(buy_time)
                target_price = buy_price * (1 + tp_rate)

                print(f"⏳ 持仓中 | 目标涨幅: {tp_rate:.2%} | 当前价: {current_price} | 目标价: {target_price:.2f}",
                      end='\r')

                if current_price >= target_price:
                    print(f"\n💰 达到动态止盈目标，执行卖出！")
                    # exchange.create_market_sell_order(SYMBOL, amount)
                    in_position = False
                    print("-" * 40)

            time.sleep(15)  # 15秒轮询一次

        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()