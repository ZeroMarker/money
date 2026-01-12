import streamlit as st
import ccxt
import pandas as pd
import time
import threading
import logging
import psutil
from datetime import datetime
import ta  # pip install ta
# 或 import talib as ta（如果安装了ta-lib）

# ---------------- 配置日志 ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- Session State 初始化 ----------------
if 'exchange' not in st.session_state:
    st.session_state.exchange = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'trades' not in st.session_state:
    st.session_state.trades = []  # 记录完成的交易

# ---------------- 侧边栏：API 配置 ----------------
st.sidebar.title("Binance API 配置")
api_key = st.sidebar.text_input("API Key", type="password")
api_secret = st.sidebar.text_input("API Secret", type="password")
testnet = st.sidebar.checkbox("使用测试网 (Testnet)", value=True)

api_key = '5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'
api_secret = 'DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'

if st.sidebar.button("连接 Binance"):
    try:
        exchange_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        }
        # if testnet:
        #     exchange_config['urls'] = {
        #         'api': {
        #             'public': 'https://demo-api.binance.com/api',
        #             'private': 'https://demo-api.binance.com/api',
        #         }
        #     }
        #     st.sidebar.info("使用 Binance Spot Demo (新 Testnet 端点)")
        # else:
        #     st.sidebar.info("使用真实 Binance 现货")

        st.session_state.exchange = ccxt.binance(exchange_config)
        st.session_state.exchange.set_sandbox_mode(True)
        balance = st.session_state.exchange.fetch_balance()
        usdt_free = balance.get('USDT', {}).get('free', 0)
        st.sidebar.success(f"连接成功！USDT 可用余额: {usdt_free:.2f}")
    except Exception as e:
        st.sidebar.error(f"连接失败: {str(e)}")
        if 'Invalid Api-Key' in str(e):
            st.sidebar.warning("建议：去 https://demo-api.binance.com 生成新的 Testnet Key（旧 testnet.vision 的 Key 可能失效）")

# ---------------- 主界面 Tabs ----------------
tab1, tab2, tab3 = st.tabs(["1. 账户信息", "2. 交易策略", "3. 系统管理"])

# ---------------- Tab 1: 账户信息 ----------------
with tab1:
    st.header("账户资产 & 交易记录")
    if st.session_state.exchange:
        try:
            balance = st.session_state.exchange.fetch_balance()
            assets = []
            for asset, info in balance.items():
                if isinstance(info, dict) and float(info.get('free', 0)) > 0:  # 强制转换为 float
                    assets.append({
                        '资产': asset,
                        '可用': float(info.get('free', 0)),
                        '锁定': float(info.get('used', 0)),
                        '总计': float(info.get('total', 0))
                    })
            df_assets = pd.DataFrame(assets)
            st.subheader("资产概览")
            if not df_assets.empty:
                st.dataframe(
                    df_assets.style.format(
                        "{:.4f}",
                        subset=['可用', '锁定', '总计']
                    )
                )
            else:
                st.info("无可用资产")

            # 最近订单/交易
            orders = st.session_state.exchange.fetch_my_trades(limit=20)
            if orders is not None:
                df_trades = pd.DataFrame(orders)
                df_trades = df_trades[['datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee']]
                df_trades['profit'] = df_trades.apply(lambda row: (row['price'] * row['amount'] if row['side'] == 'sell' else -row['cost']) - row['fee']['cost'] if row['fee'] else 0, axis=1)
                st.subheader("最近交易记录")
                st.dataframe(df_trades.sort_values('datetime', ascending=False))
            else:
                st.info("暂无交易记录")
        except Exception as e:
            st.error(f"获取账户信息失败: {e}")
    else:
        st.info("请先在侧边栏连接 API")

# ---------------- Tab 2: 交易策略 ----------------
with tab2:
    st.header("RSI 低买高卖策略 (现货)")

    col1, col2 = st.columns(2)
    with col1:
        symbol = st.selectbox("交易对", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"])
        timeframe = st.selectbox("K线周期", ["5m", "15m", "1h", "4h"])
        rsi_period = st.number_input("RSI 周期", min_value=5, max_value=30, value=14)
        rsi_overbought = st.number_input("超买阈值 (卖出)", min_value=50, max_value=90, value=70)
        rsi_oversold = st.number_input("超卖阈值 (买入)", min_value=10, max_value=50, value=30)

    with col2:
        profit_target = st.number_input("目标盈利百分比 (%)", min_value=0.5, max_value=10.0, value=2.0) / 100
        trade_usdt = st.number_input("每次交易量 (USDT)", min_value=10.0, value=100.0)
        dip_threshold = st.number_input("额外低点买入条件 (%)", min_value=0.3, value=1.0) / 100  # 可选dip买入

    def run_bot():
        exchange = st.session_state.exchange
        if not exchange:
            logger.error("未连接交易所")
            return

        in_position = False
        entry_price = 0
        while st.session_state.running:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=rsi_period + 10)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=rsi_period).rsi()

                current_price = df['close'].iloc[-1]
                current_rsi = df['rsi'].iloc[-1]

                log_msg = f"{datetime.now()} | {symbol} | 价格: {current_price:.2f} | RSI: {current_rsi:.2f}"
                st.session_state.log_messages.append(log_msg)
                logger.info(log_msg)

                if not in_position:
                    # 买入条件: RSI超卖 + 可选dip
                    prev_close = df['close'].iloc[-2]
                    if current_rsi < rsi_oversold and (current_price < prev_close * (1 - dip_threshold)):
                        amount = trade_usdt / current_price
                        order = exchange.create_market_buy_order(symbol, amount)
                        entry_price = current_price
                        in_position = True
                        trade_info = f"买入 @ {current_price:.4f} | 数量: {amount:.6f}"
                        st.session_state.log_messages.append(trade_info)
                        st.session_state.trades.append({'time': datetime.now(), 'action': 'BUY', 'price': current_price, 'amount': amount})
                        logger.info(trade_info)

                else:
                    # 卖出条件: 达到盈利目标 或 RSI超买
                    profit_pct = (current_price / entry_price) - 1
                    if profit_pct >= profit_target or current_rsi > rsi_overbought:
                        amount = exchange.fetch_balance()[symbol.split('/')[0]]['free']
                        if amount > 0:
                            order = exchange.create_market_sell_order(symbol, amount)
                            profit = (current_price - entry_price) * amount
                            trade_info = f"卖出 @ {current_price:.4f} | 盈利: {profit:.2f} USDT ({profit_pct*100:.2f}%)"
                            st.session_state.log_messages.append(trade_info)
                            st.session_state.trades.append({'time': datetime.now(), 'action': 'SELL', 'price': current_price, 'profit': profit})
                            logger.info(trade_info)
                            in_position = False

                time.sleep(60)  # 每分钟检查一次，根据timeframe调整

            except Exception as e:
                err_msg = f"错误: {e}"
                st.session_state.log_messages.append(err_msg)
                logger.error(err_msg)
                time.sleep(30)

    if st.button("一键启动策略"):
        if not st.session_state.running and st.session_state.exchange:
            st.session_state.running = True
            threading.Thread(target=run_bot, daemon=True).start()
            st.success("策略已启动！请查看日志。")
        else:
            st.warning("已在运行或未连接交易所")

    if st.button("停止策略"):
        st.session_state.running = False
        st.success("策略已停止")

    # 显示本次运行交易记录
    if st.session_state.trades:
        st.subheader("本次策略交易记录")
        st.dataframe(pd.DataFrame(st.session_state.trades))

# ---------------- Tab 3: 系统管理 ----------------
with tab3:
    st.header("系统运行情况")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("运行状态")
        status = "运行中" if st.session_state.running else "已停止"
        st.metric("策略状态", status)
        st.metric("当前时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with col2:
        st.subheader("资源占用")
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        st.metric("CPU 使用率", f"{cpu}%")
        st.metric("内存使用率", f"{mem}%")

    st.subheader("日志输出 (最新50条)")
    if st.session_state.log_messages:
        logs = st.session_state.log_messages[-50:]
        st.text_area("日志", "\n".join(logs), height=300)

    if st.button("清空日志"):
        st.session_state.log_messages = []
        st.rerun()