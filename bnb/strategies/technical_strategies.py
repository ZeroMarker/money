import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD金叉死叉策略
    当MACD线从下方穿越信号线时买入，反之卖出
    """
    
    def __init__(self, api_key, api_secret, symbol, amount_usdt,
                 fast_period=12, slow_period=26, signal_period=9):
        super().__init__(api_key, api_secret, symbol, amount_usdt)
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def calculate_macd(self, df):
        """计算MACD指标"""
        close_prices = df['c']
        
        # 计算EMA
        ema_fast = close_prices.ewm(span=self.fast_period).mean()
        ema_slow = close_prices.ewm(span=self.slow_period).mean()
        
        # 计算MACD线和信号线
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period).mean()
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]
    
    def should_buy(self, df):
        """判断是否应该买入 - MACD线上穿信号线"""
        macd_line, signal_line, histogram = self.calculate_macd(df)
        
        # 获取前一个周期的数据
        prev_macd = df['c'].ewm(span=self.fast_period).mean().shift(1) - \
                   df['c'].ewm(span=self.slow_period).mean().shift(1)
        prev_signal = prev_macd.ewm(span=self.signal_period).mean()
        
        # 检查金叉条件
        golden_cross = (prev_macd.iloc[-1] <= prev_signal.iloc[-1]) and (macd_line > signal_line)
        
        current_price = self.fetch_current_price()
        print(f"🔍 扫描中 | MACD: {macd_line:.4f} | Signal: {signal_line:.4f} | 价格: {current_price:.2f}", end='\r')
        
        return golden_cross
    
    def should_sell(self, df):
        """判断是否应该卖出 - MACD线下穿信号线"""
        macd_line, signal_line, histogram = self.calculate_macd(df)
        
        # 获取前一个周期的数据
        prev_macd = df['c'].ewm(span=self.fast_period).mean().shift(1) - \
                   df['c'].ewm(span=self.slow_period).mean().shift(1)
        prev_signal = prev_macd.ewm(span=self.signal_period).mean()
        
        # 检查死叉条件
        death_cross = (prev_macd.iloc[-1] >= prev_signal.iloc[-1]) and (macd_line < signal_line)
        
        current_price = self.fetch_current_price()
        print(f"⏳ 持仓中 | MACD: {macd_line:.4f} | Signal: {signal_line:.4f} | 价格: {current_price:.2f}", end='\r')
        
        return death_cross


class MovingAverageStrategy(BaseStrategy):
    """
    移动平均线策略
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    
    def __init__(self, api_key, api_secret, symbol, amount_usdt,
                 short_period=20, long_period=50):
        super().__init__(api_key, api_secret, symbol, amount_usdt)
        
        self.short_period = short_period
        self.long_period = long_period
    
    def calculate_ma(self, df):
        """计算移动平均线"""
        close_prices = df['c']
        ma_short = close_prices.rolling(window=self.short_period).mean()
        ma_long = close_prices.rolling(window=self.long_period).mean()
        
        return ma_short.iloc[-1], ma_long.iloc[-1]
    
    def should_buy(self, df):
        """判断是否应该买入 - 短期均线上穿长期均线"""
        ma_short, ma_long = self.calculate_ma(df)
        
        # 获取前一个周期的数据
        prev_close = df['c'].shift(1)
        prev_ma_short = prev_close.rolling(window=self.short_period).mean()
        prev_ma_long = prev_close.rolling(window=self.long_period).mean()
        
        # 检查金叉条件
        golden_cross = (prev_ma_short.iloc[-1] <= prev_ma_long.iloc[-1]) and (ma_short > ma_long)
        
        current_price = self.fetch_current_price()
        print(f"🔍 扫描中 | MA({self.short_period}): {ma_short:.2f} | MA({self.long_period}): {ma_long:.2f} | 价格: {current_price:.2f}", end='\r')
        
        return golden_cross
    
    def should_sell(self, df):
        """判断是否应该卖出 - 短期均线下穿长期均线"""
        ma_short, ma_long = self.calculate_ma(df)
        
        # 获取前一个周期的数据
        prev_close = df['c'].shift(1)
        prev_ma_short = prev_close.rolling(window=self.short_period).mean()
        prev_ma_long = prev_close.rolling(window=self.long_period).mean()
        
        # 检查死叉条件
        death_cross = (prev_ma_short.iloc[-1] >= prev_ma_long.iloc[-1]) and (ma_short < ma_long)
        
        current_price = self.fetch_current_price()
        print(f"⏳ 持仓中 | MA({self.short_period}): {ma_short:.2f} | MA({self.long_period}): {ma_long:.2f} | 价格: {current_price:.2f}", end='\r')
        
        return death_cross


class BollingerBandsStrategy(BaseStrategy):
    """
    布林带策略
    当价格触及下轨时买入，触及上轨时卖出
    """
    
    def __init__(self, api_key, api_secret, symbol, amount_usdt,
                 period=20, std_dev=2):
        super().__init__(api_key, api_secret, symbol, amount_usdt)
        
        self.period = period
        self.std_dev = std_dev
    
    def calculate_bollinger_bands(self, df):
        """计算布林带"""
        close_prices = df['c']
        
        # 计算中轨（移动平均线）
        middle_band = close_prices.rolling(window=self.period).mean()
        
        # 计算标准差
        std = close_prices.rolling(window=self.period).std()
        
        # 计算上下轨
        upper_band = middle_band + (std * self.std_dev)
        lower_band = middle_band - (std * self.std_dev)
        
        return upper_band.iloc[-1], middle_band.iloc[-1], lower_band.iloc[-1]
    
    def should_buy(self, df):
        """判断是否应该买入 - 价格触及下轨"""
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(df)
        current_price = self.fetch_current_price()
        
        # 检查价格是否触及或跌破下轨
        touch_lower = current_price <= lower_band
        
        print(f"🔍 扫描中 | 价格: {current_price:.2f} | 上轨: {upper_band:.2f} | 中轨: {middle_band:.2f} | 下轨: {lower_band:.2f}", end='\r')
        
        return touch_lower
    
    def should_sell(self, df):
        """判断是否应该卖出 - 价格触及上轨"""
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(df)
        current_price = self.fetch_current_price()
        
        # 检查价格是否触及或突破上轨
        touch_upper = current_price >= upper_band
        
        print(f"⏳ 持仓中 | 价格: {current_price:.2f} | 上轨: {upper_band:.2f} | 中轨: {middle_band:.2f} | 下轨: {lower_band:.2f}", end='\r')
        
        return touch_upper