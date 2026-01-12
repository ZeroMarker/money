import ccxt
import time
import pandas as pd
import math
from datetime import datetime
import os

# 导入我们之前写的告警函数（假设文件名为 alerts.py）
# from alerts import universal_alert

# --- 基础配置 ---
API_KEY = '你的API_KEY'
API_SECRET = '你的API_SECRET'

SYMBOL = 'BTC/USDT'
BUY_AMOUNT_USDT = 50
INITIAL_TP = 0.02
MIN_TP = 0.0035
DECAY_FACTOR = 0.15

# 初始化
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})
# 如果是真实交易，请注释掉下面这一行
exchange.set_sandbox_mode(True)


def fetch_rsi(symbol, period=14):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]
    except Exception as e:
        print(f"获取RSI失败: {e}")
        return 50  # 返回中间值防止误触发


def get_dynamic_tp(buy_time):
    hours_held = (datetime.now() - buy_time).total_seconds() / 3600
    current_tp = (INITIAL_TP - MIN_TP) * math.exp(-DECAY_FACTOR * hours_held) + MIN_TP
    return current_tp


def main():
    in_position = False
    buy_price = 0
    buy_time = None
    amount = 0

    print(f"🚀 策略启动 | 模式: {'测试网' if exchange.urls['api']['public'].find('testnet') > 0 else '实盘'}")

    while True:
        try:
            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']

            if not in_position:
                rsi = fetch_rsi(SYMBOL)
                print(f"🔍 扫描中 | RSI: {rsi:.2f} | 价格: {current_price}", end='\r')

                if rsi < 35:
                    print(f"\n📉 触发买入信号！RSI: {rsi:.2f}")

                    # 1. 计算下单量并处理精度
                    raw_amount = BUY_AMOUNT_USDT / current_price
                    amount = float(exchange.amount_to_precision(SYMBOL, raw_amount))

                    # 2. 执行真实买入 (市价单)
                    order = exchange.create_market_buy_order(SYMBOL, amount)

                    buy_price = order['price'] if order['price'] else current_price
                    buy_time = datetime.now()
                    in_position = True

                    msg = f"✅ 已买入 {SYMBOL}\n价格: {buy_price}\n数量: {amount}"
                    print(msg)
                    # universal_alert(msg) # 发送 TG/邮件告警

            else:
                tp_rate = get_dynamic_tp(buy_time)
                target_price = buy_price * (1 + tp_rate)

                print(f"⏳ 持仓中 | 目标涨幅: {tp_rate:.2%} | 目标价: {target_price:.2f}", end='\r')

                if current_price >= target_price:
                    print(f"\n💰 达到目标价 {target_price:.2f}，执行卖出！")

                    # 3. 执行真实卖出
                    # 使用上次买入的精确数量进行全平
                    exchange.create_market_sell_order(SYMBOL, amount)

                    in_position = False
                    msg = f"💵 卖出离场 {SYMBOL}\n卖出价: {current_price}\n持仓时长: {datetime.now() - buy_time}"
                    print(msg)
                    # universal_alert(msg)
                    print("-" * 40)



        except Exception as e:
            error_msg = f"❌ 运行异常: {str(e)}"
            print(f"\n{error_msg}")
            # universal_alert(error_msg)


if __name__ == "__main__":
    main()