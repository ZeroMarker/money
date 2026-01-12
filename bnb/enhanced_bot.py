from random import choice

import ccxt
import time
import pandas as pd
from datetime import datetime
from config import *
from strategies.strategy_manager import StrategyManager, AdvancedRSIStrategy


def main():
    """
    主函数 - 根据配置运行选定的策略
    """
    # 创建策略管理器
    manager = StrategyManager(
        api_key=API_KEY,
        api_secret=API_SECRET,
        symbol=SYMBOL,
        amount_usdt=BUY_AMOUNT_USDT
    )
    
    # 设置沙盒模式
    manager.strategies['rsi'].exchange.set_sandbox_mode(EXCHANGE_CONFIG['sandbox_mode'])
    manager.strategies['macd'].exchange.set_sandbox_mode(EXCHANGE_CONFIG['sandbox_mode'])
    manager.strategies['ma'].exchange.set_sandbox_mode(EXCHANGE_CONFIG['sandbox_mode'])
    manager.strategies['bb'].exchange.set_sandbox_mode(EXCHANGE_CONFIG['sandbox_mode'])
    
    print("="*60)
    print("🤖 量化交易机器人启动")
    print(f"📊 交易对: {SYMBOL}")
    print(f"💵 每次下单金额: {BUY_AMOUNT_USDT} USDT")
    print(f"🔄 轮询间隔: {SLEEP_TIME} 秒")
    print(f"🧪 沙盒模式: {EXCHANGE_CONFIG['sandbox_mode']}")
    print("="*60)
    print("可用策略:")
    for i, strategy_name in enumerate(manager.list_strategies(), 1):
        print(f"{i}. {strategy_name.upper()}")
    print("="*60)
    
    # 选择要运行的策略
    print("\n请选择要运行的策略:")
    print("1. RSI超卖策略 (原版)")
    print("2. MACD金叉死叉策略")
    print("3. 移动平均线策略")
    print("4. 布林带策略")
    print("5. 高级RSI策略 (RSI+MA组合)")
    print("6. 运行所有策略")
    
    # choice = input("\n请输入选择 (1-6): ").strip()

    choice = '2'

    if choice == '1':
        # 运行原版RSI策略
        strategy = manager.strategies['rsi']
        # 应用配置
        strategy.rsi_threshold = RSI_CONFIG['rsi_threshold']
        strategy.initial_tp = RSI_CONFIG['initial_tp']
        strategy.min_tp = RSI_CONFIG['min_tp']
        strategy.decay_factor = RSI_CONFIG['decay_factor']
        strategy.run(sleep_time=SLEEP_TIME)
        
    elif choice == '2':
        # 运行MACD策略
        strategy = manager.strategies['macd']
        # 应用配置
        strategy.fast_period = MACD_CONFIG['fast_period']
        strategy.slow_period = MACD_CONFIG['slow_period']
        strategy.signal_period = MACD_CONFIG['signal_period']
        strategy.run(sleep_time=SLEEP_TIME)
        
    elif choice == '3':
        # 运行移动平均线策略
        strategy = manager.strategies['ma']
        # 应用配置
        strategy.short_period = MA_CONFIG['short_period']
        strategy.long_period = MA_CONFIG['long_period']
        strategy.run(sleep_time=SLEEP_TIME)
        
    elif choice == '4':
        # 运行布林带策略
        strategy = manager.strategies['bb']
        # 应用配置
        strategy.period = BB_CONFIG['period']
        strategy.std_dev = BB_CONFIG['std_dev']
        strategy.run(sleep_time=SLEEP_TIME)
        
    elif choice == '5':
        # 运行高级RSI策略
        strategy = AdvancedRSIStrategy(
            api_key=API_KEY,
            api_secret=API_SECRET,
            symbol=SYMBOL,
            amount_usdt=BUY_AMOUNT_USDT,
            rsi_threshold=ADVANCED_RSI_CONFIG['rsi_threshold'],
            initial_tp=ADVANCED_RSI_CONFIG['initial_tp'],
            min_tp=ADVANCED_RSI_CONFIG['min_tp'],
            decay_factor=ADVANCED_RSI_CONFIG['decay_factor'],
            ma_short_period=ADVANCED_RSI_CONFIG['ma_short_period'],
            ma_long_period=ADVANCED_RSI_CONFIG['ma_long_period']
        )
        strategy.exchange.set_sandbox_mode(EXCHANGE_CONFIG['sandbox_mode'])
        strategy.run(sleep_time=SLEEP_TIME)
        
    elif choice == '6':
        # 运行所有策略（不推荐同时运行，因为会产生仓位冲突）
        print("⚠️  警告: 同时运行多个策略可能会导致仓位冲突！")
        confirm = input("是否继续？(y/N): ").strip().lower()
        if confirm == 'y':
            for name, strategy in manager.strategies.items():
                print(f"\n--- 运行 {name.upper()} 策略 ---")
                # 这里只是演示，实际应用中应避免同时运行多个策略
                # 因为它们会相互干扰仓位状态
                pass
        else:
            print("已取消运行所有策略")
    else:
        print("无效选择，退出程序")


if __name__ == "__main__":
    main()