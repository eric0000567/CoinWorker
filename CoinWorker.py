import asyncio
import os
import sys
from pprint import pprint
import time
from max.client import Client
import ccxt

class CoinWorker:
    def __init__(self):
        self.maxClient = Client('','')
        self.aceClient = ccxt.ace()
        self.bitoClient = ccxt.bitopro()

    def get_exchange_bids_asks(self):
        max_price = self.maxClient.get_public_pair_depth('usdttwd',1)
        ace_price = self.aceClient.fetch_order_book('USDT/TWD',1)
        bito_price = self.bitoClient.fetch_order_book('USDT/TWD',1)

        return {'max':{'sell':max_price['asks'][0][0], 'buy':max_price['bids'][0][0]},
                'ace':{'sell':ace_price['asks'][0][1], 'buy':ace_price['bids'][0][1]},
                'bito':{'sell':bito_price['asks'][0][0], 'buy':bito_price['bids'][0][0]}}

coinWorker = CoinWorker()
print(coinWorker.get_exchange_bids_asks())
