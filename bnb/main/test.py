import ccxt
import pandas as pd

# 填入你的测试网 Key
api_key = '5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'
api_secret = 'DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'

# 初始化交易所
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,  # 启用频率限制保护
    'options': {
        'defaultType': 'spot',  # 现货模式
    }
})

# 核心：开启测试网模式
# 注意：ccxt 最新版本可能需要显式设置测试网 URL，因为币安测试网近期有地址迁移
exchange.set_sandbox_mode(True)


def test_connection():
    try:
        print("--- 1. 正在检查网络连接与 API 有效性 ---")
        # 验证 API Key 权限和余额
        balance = exchange.fetch_balance()
        print("✅ 连接成功！")

        # 过滤出有余额资产
        df_balance = pd.DataFrame(balance['info']['balances'])
        df_balance['free'] = df_balance['free'].astype(float)
        active_balances = df_balance[df_balance['free'] > 0]

        print("\n--- 2. 当前账户余额 (测试网) ---")
        if not active_balances.empty:
            print(active_balances[['asset', 'free']])
        else:
            print("账户目前没有可用资金，请去币安测试网 Faucet 领取。")

        print("\n--- 3. 获取实时行情测试 ---")
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"BTC 当前价格: {ticker['last']} USDT")
        print(f"24h 涨跌幅: {ticker['percentage']}%")

    except Exception as e:
        print(f"❌ 连接失败: {e}")


if __name__ == "__main__":
    test_connection()