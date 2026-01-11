from binance import Client

api_key = '5U9dM3mSY068k3LgFfpO8tmh3YbTIbeJRQXo5Uxd0KCDSxgFeKGphcnBGHUYlWBL'
api_secret = 'DUwb9nX8lHMd1SWWIThTzCfJ5Bwz5wImviaAKWe1ZmmVpJhykDp9XFUxYl1AwU6E'

client = Client(api_key, api_secret, testnet=True)

# print(json.dumps(client.get_account(),indent=2))

symbol = 'BTCUSDT'

buy_price_threshold = 10300

sell_price_threshold = 105500

trade_quantity = 0.001


def get_current_price(symbol):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])


print(get_current_price(symbol))

def place_buy_order(symbol, quantity):
    order = client.order_market_buy(symbol=symbol,quantity=quantity)
    print(f'Buy order done: {order}')

def place_sell_order(symbol, quantity):
    order = client.order_market_sell(symbol=symbol,quantity=quantity)
    print(f'Sell order done: {order}')

ticker = client.get_symbol_ticker(symbol=symbol)
print(ticker)
