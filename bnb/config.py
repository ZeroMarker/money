# 配置文件 - 交易策略参数设置

# 基础配置
API_KEY = '5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'
API_SECRET = 'DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'
SYMBOL = 'BTC/USDT'
BUY_AMOUNT_USDT = 50  # 每次下单金额

# 通用策略配置
SLEEP_TIME = 15  # 轮询间隔（秒）

# RSI策略配置
RSI_CONFIG = {
    'rsi_threshold': 35,      # RSI超卖阈值
    'initial_tp': 0.02,       # 初始止盈目标 (2%)
    'min_tp': 0.0035,         # 最小止盈目标 (0.35%)
    'decay_factor': 0.15      # 衰减系数
}

# MACD策略配置
MACD_CONFIG = {
    'fast_period': 12,        # 快速EMA周期
    'slow_period': 26,        # 慢速EMA周期
    'signal_period': 9        # 信号线EMA周期
}

# 移动平均线策略配置
MA_CONFIG = {
    'short_period': 20,       # 短期均线周期
    'long_period': 50         # 长期均线周期
}

# 布林带策略配置
BB_CONFIG = {
    'period': 20,             # 周期
    'std_dev': 2              # 标准差倍数
}

# 高级RSI策略配置
ADVANCED_RSI_CONFIG = {
    'rsi_threshold': 35,
    'initial_tp': 0.02,
    'min_tp': 0.0035,
    'decay_factor': 0.15,
    'ma_short_period': 20,
    'ma_long_period': 50
}

# 交易所配置
EXCHANGE_CONFIG = {
    'sandbox_mode': True,     # 是否启用沙盒模式
    'rate_limit': True        # 是否启用速率限制
}