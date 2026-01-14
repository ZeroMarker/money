# 量化交易机器人增强版

基于原始 bot.py 文件开发的多策略量化交易系统，包含多种技术分析策略。

## 🚀 新增功能

### 1. 策略架构
- **BaseStrategy**: 抽象基类，定义了策略的基本接口
- **RSIStrategy**: 原始RSI超卖买入策略
- **MACDStrategy**: MACD金叉死叉策略
- **MovingAverageStrategy**: 移动平均线策略
- **BollingerBandsStrategy**: 布林带策略
- **AdvancedRSIStrategy**: 高级RSI策略（RSI+MA组合）

### 2. 策略详情

#### RSI超卖策略 (RSI Strategy)
- **买入条件**: RSI < 35 (超卖区)
- **卖出条件**: 达到动态止盈目标
- **特点**: 使用指数衰减计算动态止盈

#### MACD金叉死叉策略 (MACD Strategy)
- **买入条件**: MACD线上穿信号线（金叉）
- **卖出条件**: MACD线下穿信号线（死叉）

#### 移动平均线策略 (Moving Average Strategy)
- **买入条件**: 短期均线上穿长期均线（金叉）
- **卖出条件**: 短期均线下穿长期均线（死叉）

#### 布林带策略 (Bollinger Bands Strategy)
- **买入条件**: 价格触及或跌破下轨
- **卖出条件**: 价格触及或突破上轨

#### 高级RSI策略 (Advanced RSI Strategy)
- **买入条件**: RSI超卖 + 均线多头排列
- **卖出条件**: 达到动态止盈目标 或 RSI超买 (>70)

## 📁 项目结构

```
bnb/
├── bot.py                 # 原始版本
├── enhanced_bot.py        # 增强版主程序
├── config.py              # 配置文件
├── strategies/            # 策略模块目录
│   ├── base_strategy.py   # 基础策略类
│   ├── rsi_strategy.py    # RSI策略
│   ├── technical_strategies.py  # 技术指标策略
│   └── strategy_manager.py      # 策略管理器
```

## ⚙️ 配置选项

在 `config.py` 中可配置各种参数：

```python
# 基础配置
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
SYMBOL = 'BTC/USDT'
BUY_AMOUNT_USDT = 50

# RSI策略配置
RSI_CONFIG = {
    'rsi_threshold': 35,      # RSI超卖阈值
    'initial_tp': 0.02,       # 初始止盈目标 (2%)
    'min_tp': 0.0035,         # 最小止盈目标 (0.35%)
    'decay_factor': 0.15      # 衰减系数
}

# 其他策略也有相应配置...
```

## 🛠️ 使用方法

1. 安装依赖：
```bash
pip install ccxt pandas numpy
```

2. 运行增强版机器人：
```bash
python enhanced_bot.py
```

3. 根据提示选择要运行的策略

## ⚠️ 注意事项

- 请确保在沙盒环境中测试，避免真实资金损失
- 同时运行多个策略会导致仓位冲突，不建议这样做
- 根据市场情况调整参数以获得最佳效果
- 交易有风险，投资需谨慎

## 🔧 自定义策略

如需添加新策略，继承 `BaseStrategy` 类并实现 `should_buy()` 和 `should_sell()` 方法即可。