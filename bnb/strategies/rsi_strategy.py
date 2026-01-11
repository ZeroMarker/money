import pandas as pd
import numpy as np
from datetime import datetime
from strategies.base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI超卖买入策略
    当RSI低于阈值时买入，达到动态止盈目标时卖出
    """
    
    def __init__(self, api_key, api_secret, symbol, amount_usdt, 
                 rsi_threshold=35, initial_tp=0.02, min_tp=0.0035, decay_factor=0.15):
        super().__init__(api_key, api_secret, symbol, amount_usdt)
        
        self.rsi_threshold = rsi_threshold  # RSI超卖阈值
        self.initial_tp = initial_tp      # 初始止盈目标
        self.min_tp = min_tp              # 最小止盈目标
        self.decay_factor = decay_factor  # 衰减系数
    
    def calculate_rsi(self, df, period=14):
        """计算RSI指标"""
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def get_dynamic_tp(self):
        """计算动态止盈目标"""
        if not self.buy_time:
            return self.initial_tp
            
        hours_held = (datetime.now() - self.buy_time).total_seconds() / 3600
        import math
        current_tp = (self.initial_tp - self.min_tp) * math.exp(-self.decay_factor * hours_held) + self.min_tp
        return max(current_tp, self.min_tp)  # 确保不低于最小止盈目标
    
    def should_buy(self, df):
        """判断是否应该买入 - RSI低于阈值"""
        rsi = self.calculate_rsi(df)
        print(f"🔍 扫描中 | RSI: {rsi:.2f} | 价格: {self.fetch_current_price():.2f}", end='\r')
        return rsi < self.rsi_threshold
    
    def should_sell(self, df):
        """判断是否应该卖出 - 达到动态止盈目标"""
        current_price = self.fetch_current_price()
        dynamic_tp = self.get_dynamic_tp()
        target_price = self.buy_price * (1 + dynamic_tp)
        
        print(f"⏳ 持仓中 | 目标涨幅: {dynamic_tp:.2%} | 当前价: {current_price:.2f} | 目标价: {target_price:.2f}",
              end='\r')
        
        return current_price >= target_price