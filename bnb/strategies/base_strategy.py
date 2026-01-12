import ccxt
import time
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime


class BaseStrategy(ABC):
    """
    基础交易策略抽象类
    """
    
    def __init__(self, api_key, api_secret, symbol, amount_usdt, exchange_params=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.amount_usdt = amount_usdt
        
        # 默认交易所参数
        default_params = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }
        
        if exchange_params:
            default_params.update(exchange_params)
            
        self.exchange = ccxt.binance(default_params)
        
        # 状态变量
        self.in_position = False
        self.buy_price = 0
        self.buy_time = None
        self.amount = 0
        
    def fetch_ohlcv(self, timeframe='5m', limit=100):
        """获取OHLCV数据"""
        return self.exchange.fetch_ohlcv(self.symbol, timeframe=timeframe, limit=limit)
    
    def fetch_current_price(self):
        """获取当前价格"""
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker['last']
    
    def calculate_amount(self, price):
        """根据价格计算购买数量"""
        return self.amount_usdt / price
    
    @abstractmethod
    def should_buy(self, df):
        """判断是否应该买入"""
        pass
    
    @abstractmethod
    def should_sell(self, df):
        """判断是否应该卖出"""
        pass
    
    def execute_buy(self):
        """执行买入操作"""
        current_price = self.fetch_current_price()
        self.amount = self.calculate_amount(current_price)

        try:
            # 实际下单
            order = self.exchange.create_market_buy_order(self.symbol, self.amount)

            # 检查订单是否成功执行
            if order and 'status' in order and order['status'] in ['closed', 'filled']:
                self.buy_price = order['average'] if order['average'] else current_price
                self.buy_time = datetime.now()
                self.in_position = True
                self.amount = order['filled']  # 更新为实际成交数量

                return {
                    'action': 'BUY',
                    'price': self.buy_price,
                    'amount': self.amount,
                    'order_id': order['id'],
                    'timestamp': self.buy_time
                }
            else:
                print(f"❌ 买单未完全成交或失败: {order}")
                return None
        except Exception as e:
            print(f"❌ 买入订单执行失败: {e}")
            return None
    
    def execute_sell(self):
        """执行卖出操作"""
        current_price = self.fetch_current_price()

        try:
            # 实际下单
            order = self.exchange.create_market_sell_order(self.symbol, self.amount)

            # 检查订单是否成功执行
            if order and 'status' in order and order['status'] in ['closed', 'filled']:
                sell_price = order['average'] if order['average'] else current_price
                profit = ((sell_price - self.buy_price) / self.buy_price) * 100
                holding_time = datetime.now() - self.buy_time if self.buy_time else None

                self.in_position = False
                self.buy_price = 0
                self.buy_time = None
                self.amount = 0

                return {
                    'action': 'SELL',
                    'price': sell_price,
                    'profit': profit,
                    'order_id': order['id'],
                    'holding_time': holding_time
                }
            else:
                print(f"❌ 卖单未完全成交或失败: {order}")
                return None
        except Exception as e:
            print(f"❌ 卖出订单执行失败: {e}")
            return None
    
    def run(self, sleep_time=15):
        """运行策略主循环"""
        print(f"开始运行 {self.__class__.__name__} 策略... 交易对: {self.symbol}")

        while True:
            try:
                # 获取市场数据
                ohlcv = self.fetch_ohlcv()
                df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])

                current_price = self.fetch_current_price()

                if not self.in_position:
                    # 检查买入信号
                    if self.should_buy(df):
                        result = self.execute_buy()
                        if result:
                            print(f"\n📈 {result['action']}信号触发！价格: {result['price']:.2f}")
                            print(f"✅ 已买入 | 均价: {result['price']:.2f} | 数量: {result['amount']:.6f} | 订单ID: {result['order_id']}")
                        else:
                            print(f"\n❌ 买入失败，请检查账户余额或网络连接")

                    # 显示当前状态
                    else:
                        self.display_status('scanning', current_price)

                else:
                    # 检查卖出信号
                    if self.should_sell(df):
                        result = self.execute_sell()
                        if result:
                            print(f"\n📉 {result['action']}信号触发！价格: {result['price']:.2f}")
                            print(f"✅ 已卖出 | 价格: {result['price']:.2f} | 收益: {result['profit']:.2f}% | 订单ID: {result['order_id']}")
                            print("-" * 50)
                        else:
                            print(f"\n❌ 卖出失败，请检查持仓或网络连接")

                    # 显示持仓状态
                    else:
                        self.display_status('holding', current_price)

                time.sleep(sleep_time)

            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                time.sleep(10)
    
    def display_status(self, status, current_price):
        """显示当前状态"""
        if status == 'scanning':
            print(f"🔍 扫描中 | 价格: {current_price:.2f}", end='\r')
        elif status == 'holding':
            if self.buy_time:
                elapsed = datetime.now() - self.buy_time
                print(f"⏳ 持仓中 | 买入价: {self.buy_price:.2f} | 当前价: {current_price:.2f} | "
                      f"收益: {((current_price - self.buy_price) / self.buy_price) * 100:.2f}% | "
                      f"持有时间: {elapsed}", end='\r')