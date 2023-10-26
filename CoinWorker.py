import asyncio
import time
from datetime import datetime
from max.client import Client
import pandas as pd
import ccxt.async_support as ccxt_async

message_columns = ['time', 'pair', 'sell_price', 'buy_price', 'order_size', 'earn', 'total_profit']
arbitrage_path = './arbitrage_history.csv'

class CoinWorker:
    def __init__(self,pair=['USDT','TWD']):
        self.pair = pair
        self.maxClient = Client('','')
        self.aceClient = ccxt_async.ace()
        self.bitoClient = ccxt_async.bitopro()
        self.exchangs_fees = [self.maxClient.get_public_vip_levels()[0]['taker_fee'],
                            self.aceClient.fees['trading']['taker'],
                            self.bitoClient.fees['trading']['taker']]
        self.exchanges_name = ['max', 'ace', 'bito']
        self.min_order_size = 0.05
        self.total_profit = 0
    
    async def fetch_max_order_book(self):
        loop = asyncio.get_event_loop()
        max_price = await loop.run_in_executor(None, self.maxClient.get_public_pair_depth, self.pair[0]+self.pair[1], 1)
        return max_price

    async def get_exchange_bids_asks(self):
        max_price_future = asyncio.create_task(self.fetch_max_order_book())
        ace_price_future = asyncio.create_task(self.aceClient.fetch_order_book(self.pair[0]+"/"+self.pair[1],1))
        bito_price_future = asyncio.create_task(self.bitoClient.fetch_order_book(self.pair[0]+"/"+self.pair[1],1))

        max_price = await max_price_future
        ace_price = await ace_price_future
        bito_price = await bito_price_future


        return [{'asks':max_price['asks'][0], 'bids':max_price['bids'][0]},
                {'asks':ace_price['asks'][0][::-1], 'bids':ace_price['bids'][0][::-1]},
                {'asks':bito_price['asks'][0], 'bids':bito_price['bids'][0]}]


    async def bot(self):
        exchange_price = await self.get_exchange_bids_asks()

        asks_price_list = [float(s['asks'][0]) for s in exchange_price]
        asks_size_list = [float(s['asks'][1]) for s in exchange_price]
        bids_price_list = [float(b['bids'][0]) for b in exchange_price]
        bids_size_list = [float(b['bids'][1]) for b in exchange_price]


        
        buy_price = min(asks_price_list)
        sell_price = max(bids_price_list)

        order_size = min(asks_size_list[asks_price_list.index(buy_price)],
                         bids_size_list[bids_price_list.index(sell_price)],
                         self.min_order_size)
        
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
            self.total_profit += profit
            history = pd.DataFrame([[record_time, self.pair[0]+'/'+self.pair[1], sell_price, buy_price, order_size, profit, self.total_profit]])
            print(f"{record_time} {self.pair[0]+'/'+self.pair[1]} arbitrage coming!!!\n sell price in {sell_exchange_name}: {sell_price}\n buy price in {buy_exchange_name}: {buy_price}  \n order size: {order_size} \n earn: NT${profit}")
            history.to_csv(arbitrage_path, mode='a')
        else:
            print(f"{record_time} {self.pair[0]+'/'+self.pair[1]} no arbitrage opportunity\n sell price in {sell_exchange_name}: {sell_price}\n buy price in {buy_exchange_name}: {buy_price} \n spread: {profit}")
        print(f" total profit {self.pair[1]}$: {self.total_profit} ")

    async def close(self):
        await self.aceClient.close()
        await self.bitoClient.close()

async def main():
    wait_time = 2
    start_time = datetime.now()
    coinWorker = CoinWorker(['ETH','TWD'])
    print("Starting bot")
    pd.DataFrame(columns=message_columns).to_csv(arbitrage_path, mode='w')
    while True:
        try:
            total_time = datetime.now() - start_time
            print(f"running time: {total_time}")
            await coinWorker.bot()
            print('--'*50)
        except e:
            print("Exception: ", e)
            await coinWorker.close()

        await asyncio.sleep(wait_time)

asyncio.run(main())
