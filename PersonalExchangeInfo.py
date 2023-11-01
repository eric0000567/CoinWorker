import ccxt.async_support as ccxt_async
from max.client import Client

class PersonalExchangeInfo:
    def __init__(self, user_name) -> None:
        self.user_name = user_name
        self.support_exchange_name = ['max', 'ace', 'bitopro']
        self.registered_exchange = {}
        [self.register_exchange_key_secret(exchangeName) for exchangeName in self.support_exchange_name]
    
    def register_exchange_key_secret(self, exchangeName: str, apiKey="", apiSecret=""):
        try:
            if exchangeName.lower() == 'max':
                self.registered_exchange[exchangeName] = Client(apiKey, apiSecret)
            else:
                aceClient = getattr(ccxt_async, exchangeName)()
                aceClient.apiKey = apiKey
                aceClient.secret = apiSecret
                self.registered_exchange[exchangeName] = aceClient

        except AttributeError:
            print(f"交易所 {exchangeName} 不存在或不支持")

    def get_exchanges_fee(self):
        exchanges_fees = [self.registered_exchange['max'].get_public_vip_levels()[0]['taker_fee']]
        exchanges_fees += [ self.registered_exchange[name].fees['trading']['taker'] for name in self.support_exchange_name[1:]]
        return exchanges_fees
    
    async def post_market_order(self, exchangeName, pair, side, size):
        if exchangeName == 'max':
            #TODO: 要大於250twd才能交易測試
            return self.registered_exchange['max'].set_private_create_order(pair[0]+pair[1], side, size, 1, _type='market')
        else:
            return await self.registered_exchange[exchangeName].create_market_order(f"{pair[0]}/{pair[1]}", side, size)
    
    async def get_order_detail(self,exchangeName, id):
        #TODO: MAX下單之後回傳的訊息就包含state, avg_price, executed_volume了 可能不用這個function
        if exchangeName == 'max':
            return self.registered_exchange['max'].get_private_order_detail(id)
        else:
            return await self.registered_exchange[exchangeName].fetch_order(id)

import asyncio

async def test():
    test = PersonalExchangeInfo('test')
    
    sellOrder = asyncio.create_task(test.post_market_order('max',['MAX','TWD'], 'sell', 25))
    buyOrder = asyncio.create_task(test.post_market_order('ace',['USDT','TWD'], 'buy', 20))

    sellState = await sellOrder
    buyState = await buyOrder
    print(sellState)
    print(buyState)

    # sellOrderDetail = asyncio.create_task(test.get_order_detail('ace',sellState['id']))
    # buyOrderDetail = asyncio.create_task(test.get_order_detail('ace', buyState['id']))

    # sellReturn = await sellOrderDetail
    # buyReturn = await buyOrderDetail

    # print(f"{sellReturn}-----{buyReturn}")

asyncio.run(test())

