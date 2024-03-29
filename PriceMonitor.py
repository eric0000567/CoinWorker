import asyncio
from max.client import Client
import ccxt.async_support as ccxt_async

class PriceMointor:
    def __init__(self):
        self.exchanges_client = {'max': Client('',''),
                                 'ace': ccxt_async.ace(),
                                 'bitopro': ccxt_async.bitopro()}
        self.exchanges_name = [name for name in self.exchanges_client]
        self.exchangs_fees = {name:self.exchanges_client[name].fees['trading']['taker'] for name in self.exchanges_name[1:]}
        self.exchangs_fees['max'] = self.exchanges_client['max'].get_public_vip_levels()[0]['taker_fee']
        self.lowest_amount = {'USDT':15,
                              'TWD':500,
                              'BTC':0.0003003,
                              'ETH':0.002}
        self.min_unit_precision = {'BTCTWD':8,
                                   'ETHTWD':6,
                                   'USDTTWD':2,
                                   'BTCUSDT':6,
                                   'ETHUSDT':5,
                                   'ETHBTC':4}
    
    async def fetch_max_order_book(self, pair_one="BTC", pair_two="USDT"):
        return self.exchanges_client['max'].get_public_pair_depth(pair_one+pair_two, 1)

    async def get_exchange_bids_asks(self, pair_one="BTC", pair_two="USDT"):
        #TODO: 需優化，要可動態調整
        max_price_future = asyncio.create_task(self.fetch_max_order_book(pair_one, pair_two))
        ace_price_future = asyncio.create_task(self.exchanges_client['ace'].fetch_order_book(pair_one+"/"+pair_two,1))
        bito_price_future = asyncio.create_task(self.exchanges_client['bitopro'].fetch_order_book(pair_one+"/"+pair_two,1))

        max_price = await max_price_future
        ace_price = await ace_price_future
        bito_price = await bito_price_future


        return [{'asks':max_price['asks'][0], 'bids':max_price['bids'][0]},
                {'asks':ace_price['asks'][0][::-1], 'bids':ace_price['bids'][0][::-1]},
                {'asks':bito_price['asks'][0], 'bids':bito_price['bids'][0]}]

    async def trade_signal(self, pair=['USDT','TWD'], min_order_size = 0.001):
        exchange_price = await self.get_exchange_bids_asks(pair[0], pair[1])

        asks_price_list = [float(s['asks'][0]) for s in exchange_price]
        asks_size_list = [float(s['asks'][1]) for s in exchange_price]
        bids_price_list = [float(b['bids'][0]) for b in exchange_price]
        bids_size_list = [float(b['bids'][1]) for b in exchange_price]
        
        buy_price = min(asks_price_list)
        sell_price = max(bids_price_list)

        sell_order = asks_size_list[asks_price_list.index(buy_price)]
        buy_order = bids_size_list[bids_price_list.index(sell_price)]
        # 四捨五入最小單位
        order_size = round(min(sell_order,
                         buy_order,
                         min_order_size),self.min_unit_precision[pair[0]+pair[1]])

        buy_exchange_name = self.exchanges_name[asks_price_list.index(buy_price)]
        sell_exchange_name = self.exchanges_name[bids_price_list.index(sell_price)]
        
        buy_amount = buy_price*order_size
        sell_amount = sell_price*order_size
        #TODO 測試用：殘值計算，如果交易額度沒有達到最低要求不要購買
        if buy_amount < self.lowest_amount[pair[1].upper()] and sell_amount < self.lowest_amount[pair[1].upper()] :
            # print(f"{pair[0]+'/'+pair[1]} sell {sell_exchange_name}:{sell_price} buy {buy_exchange_name}:{buy_price} \n sell order size: {sell_amount} or buy order size: {buy_amount} need bigger than {self.lowest_amount[pair[1].upper()]}")
            return None
        
        profit = self.spread_profit_counter(sell_exchange_name,
                                            sell_price,
                                            buy_exchange_name,
                                            buy_price,
                                            order_size)

        if (profit > 0):
            result = {'pair':pair,
                      'size':order_size,
                      'buy':{'ex_name':buy_exchange_name,
                             'price':buy_price,
                             'order_size':buy_order},
                      'sell':{'ex_name':sell_exchange_name,
                             'price':sell_price,
                             'order_size':sell_order}}
            print(f"{pair[0]+'/'+pair[1]} sell {sell_exchange_name}:{sell_price} buy {buy_exchange_name}:{buy_price} order size: {order_size} \n earn: {pair[1]}${profit}")
            return result
        # print(f"{pair[0]+'/'+pair[1]} sell {sell_exchange_name}:{sell_price} buy {buy_exchange_name}:{buy_price} \n spread: {profit}")
        return None

    def spread_profit_counter(self, sell_exchange_name, sell_price, buy_exchange_name, buy_price, order_size):
        buy_fee = order_size * buy_price * float(self.exchangs_fees[buy_exchange_name])
        sell_fee = order_size * sell_price * self.exchangs_fees[sell_exchange_name]
        # #TODO 測試中暫時移除未來要放回去：殘值計算，如果交易額度沒有達到最低要求不要購買
        # buy_amount = buy_price*order_size
        # sell_amount = sell_price*order_size
        # if buy_amount < self.lowest_amount[pair[1].upper()] and sell_amount < self.lowest_amount[pair[1].upper()] :
        #     print(f"{pair[0]+'/'+pair[1]} sell {sell_exchange_name}:{sell_price} buy {buy_exchange_name}:{buy_price} \n sell order size: {sell_amount} or buy order size: {buy_amount} need bigger than {self.lowest_amount[pair[1].upper()]}")
        #     return None
        return ((sell_price - buy_price) * order_size) - (buy_fee + sell_fee)

    async def close(self):
        [await self.exchanges_client[i].close() for i in self.exchanges_name[1:]]
