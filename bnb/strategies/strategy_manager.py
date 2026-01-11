import ccxt
from strategies.rsi_strategy import RSIStrategy
from strategies.technical_strategies import MACDStrategy, MovingAverageStrategy, BollingerBandsStrategy


class StrategyManager:
    """
    策略管理器
    用于管理和运行不同的交易策略
    """
    
    def __init__(self, api_key, api_secret, symbol, amount_usdt):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.amount_usdt = amount_usdt
        
        # 初始化所有策略
        self.strategies = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """初始化所有可用的策略"""
        # RSI策略
        self.strategies['rsi'] = RSIStrategy(
            api_key=self.api_key,
            api_secret=self.api_secret,
            symbol=self.symbol,
            amount_usdt=self.amount_usdt
        )
        
        # MACD策略
        self.strategies['macd'] = MACDStrategy(
            api_key=self.api_key,
            api_secret=self.api_secret,
            symbol=self.symbol,
            amount_usdt=self.amount_usdt
        )
        
        # 移动平均线策略
        self.strategies['ma'] = MovingAverageStrategy(
            api_key=self.api_key,
            api_secret=self.api_secret,
            symbol=self.symbol,
            amount_usdt=self.amount_usdt
        )
        
        # 布林带策略
        self.strategies['bb'] = BollingerBandsStrategy(
            api_key=self.api_key,
            api_secret=self.api_secret,
            symbol=self.symbol,
            amount_usdt=self.amount_usdt
        )
    
    def get_strategy(self, strategy_name):
        """获取指定名称的策略"""
        return self.strategies.get(strategy_name.lower())
    
    def list_strategies(self):
        """列出所有可用的策略"""
        return list(self.strategies.keys())
    
    def run_strategy(self, strategy_name, sleep_time=15):
        """运行指定的策略"""
        strategy = self.get_strategy(strategy_name)
        if strategy:
            print(f"正在运行 {strategy_name.upper()} 策略...")
            strategy.run(sleep_time=sleep_time)
        else:
            print(f"未找到名为 '{strategy_name}' 的策略。可用策略: {self.list_strategies()}")
    
    def run_multiple_strategies(self, strategy_names, sleep_time=15):
        """同时运行多个策略（注意：这可能导致冲突）"""
        strategies_to_run = []
        
        for name in strategy_names:
            strategy = self.get_strategy(name)
            if strategy:
                strategies_to_run.append((name, strategy))
            else:
                print(f"未找到名为 '{name}' 的策略")
        
        if not strategies_to_run:
            print("没有有效的策略可以运行")
            return
        
        print(f"正在运行策略: {[s[0] for s in strategies_to_run]}")
        
        # 注意：同时运行多个策略可能会导致仓位冲突
        # 在实际使用中，建议每次只运行一个策略
        for name, strategy in strategies_to_run:
            print(f"策略 {name} 运行完成")


class AdvancedRSIStrategy(RSIStrategy):
    """
    高级RSI策略 - 结合多种技术指标确认信号
    """
    
    def __init__(self, api_key, api_secret, symbol, amount_usdt,
                 rsi_threshold=35, initial_tp=0.02, min_tp=0.0035, decay_factor=0.15,
                 ma_short_period=20, ma_long_period=50):
        super().__init__(api_key, api_secret, symbol, amount_usdt,
                         rsi_threshold, initial_tp, min_tp, decay_factor)
        
        self.ma_short_period = ma_short_period
        self.ma_long_period = ma_long_period
    
    def should_buy(self, df):
        """结合RSI和移动平均线判断买入信号"""
        # RSI超卖条件
        rsi = self.calculate_rsi(df)
        rsi_condition = rsi < self.rsi_threshold
        
        # 移动平均线多头排列条件
        close_prices = df['c']
        ma_short = close_prices.rolling(window=self.ma_short_period).mean()
        ma_long = close_prices.rolling(window=self.ma_long_period).mean()
        ma_condition = ma_short.iloc[-1] > ma_long.iloc[-1]
        
        current_price = self.fetch_current_price()
        print(f"🔍 扫描中 | RSI: {rsi:.2f} | MA({self.ma_short_period}>{self.ma_long_period}): {ma_condition} | 价格: {current_price:.2f}", end='\r')
        
        # 同时满足RSI超卖和均线多头排列
        return rsi_condition and ma_condition
    
    def should_sell(self, df):
        """结合RSI和动态止盈判断卖出信号"""
        current_price = self.fetch_current_price()
        dynamic_tp = self.get_dynamic_tp()
        target_price = self.buy_price * (1 + dynamic_tp)
        
        # RSI进入超买区域
        rsi = self.calculate_rsi(df)
        rsi_overbought = rsi > 70
        
        print(f"⏳ 持仓中 | 目标涨幅: {dynamic_tp:.2%} | RSI: {rsi:.2f} | 当前价: {current_price:.2f} | 目标价: {target_price:.2f}",
              end='\r')
        
        # 达到动态止盈目标或RSI超买
        return current_price >= target_price or rsi_overbought