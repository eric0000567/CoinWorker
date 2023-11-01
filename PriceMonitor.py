import asyncio
import time
from datetime import datetime
from max.client import Client
import pandas as pd
import ccxt.async_support as ccxt_async
from PersonalExchangeInfo import PersonalExchangeInfo

class PriceMointor:
    def __init__(self, exchanges: PersonalExchangeInfo):
        self.exchanges = exchanges
        self.maxClient: Client= exchanges.registered_exchange['max']
        self.aceClient: ccxt_async = exchanges.registered_exchange['ace']
        self.bitoClient: ccxt_async = exchanges.registered_exchange['bitopro']
        self.exchangs_fees = exchanges.get_exchanges_fee()
        self.exchanges_name = exchanges.support_exchange_name
    
    async def fetch_max_order_book(self, pairOne="BTC", pairTwo="USDT"):
        loop = asyncio.get_event_loop()
        max_price = await loop.run_in_executor(None, self.maxClient.get_public_pair_depth, pairOne+pairTwo, 1)
        return max_price

    async def get_exchange_bids_asks(self, pairOne="BTC", pairTwo="USDT"):
        max_price_future = asyncio.create_task(self.fetch_max_order_book(pairOne, pairTwo))
        ace_price_future = asyncio.create_task(self.aceClient.fetch_order_book(pairOne+"/"+pairTwo,1))
        bito_price_future = asyncio.create_task(self.bitoClient.fetch_order_book(pairOne+"/"+pairTwo,1))

        max_price = await max_price_future
        ace_price = await ace_price_future
        bito_price = await bito_price_future


        return [{'asks':max_price['asks'][0], 'bids':max_price['bids'][0]},
                {'asks':ace_price['asks'][0][::-1], 'bids':ace_price['bids'][0][::-1]},
                {'asks':bito_price['asks'][0], 'bids':bito_price['bids'][0]}]


    async def bot(self, pair=['USDT','TWD'], min_order_size = 0.001):
        exchange_price = await self.get_exchange_bids_asks(pair[0], pair[1])

        asks_price_list = [float(s['asks'][0]) for s in exchange_price]
        asks_size_list = [float(s['asks'][1]) for s in exchange_price]
        bids_price_list = [float(b['bids'][0]) for b in exchange_price]
        bids_size_list = [float(b['bids'][1]) for b in exchange_price]


        
        buy_price = min(asks_price_list)
        sell_price = max(bids_price_list)

        order_size = min(asks_size_list[asks_price_list.index(buy_price)],
                         bids_size_list[bids_price_list.index(sell_price)],
                         min_order_size)
        
        buy_exchange_fee = float(self.exchangs_fees[asks_price_list.index(buy_price)])
        buy_exchange_name = self.exchanges_name[asks_price_list.index(buy_price)]

        buy_fee = order_size * buy_price * buy_exchange_fee

        sell_exchange_fee = float(self.exchangs_fees[bids_price_list.index(sell_price)])
        sell_exchange_name = self.exchanges_name[bids_price_list.index(sell_price)]
        sell_fee = order_size * sell_price * sell_exchange_fee

        price_profit = sell_price - buy_price
        profit = (price_profit * order_size) - (buy_fee + sell_fee)

        record_time = time.strftime('%X')
        if (profit > 0):
            history = pd.DataFrame([[record_time, pair[0]+'/'+pair[1], sell_price, buy_price, order_size, profit]])
            sellOrder = asyncio.create_task(self.exchanges.post_market_order(sell_exchange_name, pair, 'sell', order_size))
            buyOrder = asyncio.create_task(self.exchanges.post_market_order(buy_exchange_name, pair, 'buy', order_size))
            
            sellState = await sellOrder
            buyState = await buyOrder
            #TODO: 回傳值要計算利潤？但有需要那麼多東西在bot嗎？

            print(f"{record_time} {pair[0]+'/'+pair[1]} arbitrage coming!!!\n sell price in {sell_exchange_name}: {sell_price}\n buy price in {buy_exchange_name}: {buy_price}  \n order size: {order_size} \n earn: {pair[1]}${profit}")
            return history
        else:
            print(f"{record_time} {pair[0]+'/'+pair[1]} no arbitrage opportunity\n sell price in {sell_exchange_name}: {sell_price}\n buy price in {buy_exchange_name}: {buy_price} \n spread: {profit}")
        return None


    async def close(self):
        await self.aceClient.close()
        await self.bitoClient.close()
