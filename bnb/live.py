import ccxt
import pandas as pd
import os

# ====================================================
# 配置区域
# ====================================================
# api_key = '5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'
# api_secret = 'DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'

api_key = os.getenv("binance__api_key")
api_secret = os.getenv("binance__api_secret")
telegram_bot_token = os.getenv("telegram__bot_token")
telegram_chat_id = os.getenv("telegram__chat_id")

# 初始化交易所 (Binance Testnet)
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',  # 现货模式
    }
})

# 开启测试网模式
# exchange.set_sandbox_mode(True)


def get_account_summary():
    """1. 检查连接与账户余额"""
    try:
        print("\n" + "=" * 50)
        print("正在获取账户信息...")
        balance = exchange.fetch_balance()

        # 转换为 DataFrame 展示有余额的资产
        df_balance = pd.DataFrame(balance['info']['balances'])
        df_balance['free'] = df_balance['free'].astype(float)
        active_balances = df_balance[df_balance['free'] > 0]

        if not active_balances.empty:
            print("【当前账户余额】")
            print(active_balances[['asset', 'free']])
        else:
            print("⚠️ 账户目前没有可用资金。")
    except Exception as e:
        print(f"❌ 连接失败: {e}")


def fetch_recent_trades_analysis(symbol='BTC/USDT', limit=10):
    """2. 获取最近成交并计算盈亏"""
    try:
        print("\n" + "=" * 50)
        print(f"正在获取 {symbol} 最近 {limit} 笔成交记录...")

        # 获取成交历史 (My Trades)
        trades = exchange.fetch_my_trades(symbol, limit=limit)

        if not trades:
            print(f"ℹ️ 未发现 {symbol} 的成交记录。")
            return

        # 构建 DataFrame
        data = []
        for t in trades:
            data.append({
                '时间': t['datetime'],
                '方向': '买入' if t['side'] == 'buy' else '卖出',
                '价格': t['price'],
                '数量': t['amount'],
                '总额(USDT)': t['cost'],
                '手续费': t['fee']['cost'] if t['fee'] else 0,
                '费率币种': t['fee']['currency'] if t['fee'] else ''
            })

        df = pd.DataFrame(data)
        print(df.to_string(index=False))

        # --- 盈亏统计逻辑 ---
        # 注意：这里的盈亏是基于这10笔成交的现金流统计
        buys = df[df['方向'] == '买入']['总额(USDT)'].sum()
        sells = df[df['方向'] == '卖出']['总额(USDT)'].sum()
        fees = df['手续费'].sum()  # 简化处理：假设手续费都是同一币种或折算

        net_cash_flow = sells - buys - fees

        print("\n【最近10笔交易统计】")
        print(f"● 总买入支出: {buys:.2f} USDT")
        print(f"● 总卖出收入: {sells:.2f} USDT")
        print(f"● 累计手续费: {fees:.4f} (参考计费币种)")
        print(f"● 净现金流: {net_cash_flow:.2f} USDT")

        if net_cash_flow > 0:
            print("📈 盈利状态")
        else:
            print("📉 亏损或持仓中")

    except Exception as e:
        print(f"❌ 获取订单分析失败: {e}")


# ====================================================
# 执行主程序
# ====================================================
if __name__ == "__main__":
    # 1. 检查账户余额
    get_account_summary()

    # 2. 获取行情（可选）
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"\n[实时价格] BTC/USDT: {ticker['last']}")
    except:
        pass

    # 3. 分析最近十笔成交
    fetch_recent_trades_analysis('BTC/USDT', limit=10)