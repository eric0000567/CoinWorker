from max.client import Client
import ccxt.async_support as ccxt_async  # noqa: E402
import ccxt
import asyncio
max_client = Client('','')
ace_client = ccxt.ace()
bito_client = ccxt.bitopro()

aceAsync = ccxt_async.ace({'apiKey':'', 'secret':''})

async def main():
    ace_order = await aceAsync.create_market_order('BTC/TWD','buy',0.001)
    print(ace_order)
    await aceAsync.close()

asyncio.run(main())

# address = max_client.get_private_withdrawal_addresses('USDT')
# print(address)
# 提領是可以成功的
# send_address = max_client.set_private_create_withdrawal('USDT','5','TAnK256mi9svBE6D1pZCgSZVEeNuuK6TFY')
# print(send_address)
# max_price = max_client.get_public_pair_depth('usdttwd',1)
# ace_price = ace_client.fetch_order_book('USDT/TWD',1)
# bito_price = bito_client.fetch_order_book('USDT/TWD',1)

# all = {'max':{'sell':max_price['asks'][0], 'buy':max_price['bids'][0]},# 0:price, 1:size
#                 'ace':{'sell':ace_price['asks'][0][::-1], 'buy':ace_price['bids'][0][::-1]}, #0: size, 1: price
#                 'bito':{'sell':bito_price['asks'][0], 'buy':bito_price['bids'][0]}}# 0:price, 1:size
# sell_price_list = [all[s]['sell'][0] for s in all]
# sell_size_list = [all[s]['sell'][1] for s in all]
# buy_price_list = [all[b]['buy'][0] for b in all]
# buy_size_list = [all[b]['buy'][1] for b in all]


# print(max_price['bids'][0]," ", max_price['asks'][0])
# print(ace_price['bids'][0]," ", ace_price['asks'][0])
# print(bito_price['bids'][0]," ", bito_price['asks'][0])
# print(max_price)
# print(ace_price)
# print(bito_price)

# print(max_client.get_public_vip_levels()[0])
# print('---'*10)
# print(ace_client.fees['trading']['taker'])
# print('---'*10)
# print(bito_client.fees['trading']['taker'])
# print('---'*10)
