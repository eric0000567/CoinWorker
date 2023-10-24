from max.client import Client
# import ccxt.async_support as ccxt  # noqa: E402
import ccxt
client = Client('','')
max_price = client.get_public_pair_depth('usdttwd',1)
ace_price = ccxt.ace().fetch_order_book('USDT/TWD',1)
bito_price = ccxt.bitopro().fetch_order_book('USDT/TWD',1)
print(max_price['bids']," ", max_price['asks'])
print(ace_price['bids']," ", ace_price['asks'])
print(bito_price['bids'][0]," ", bito_price['asks'])