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

    
    async def post_market_order(self, exchangeName, pair, side, size, price):
        if exchangeName == 'max':
            #TODO: 要大於250twd才能交易測試
            return self.registered_exchange['max'].set_private_create_order(pair[0]+pair[1], side, size, price, _type='market')
        else:
            return await self.registered_exchange[exchangeName].create_market_order(f"{pair[0]}/{pair[1]}", side, size, price)
    
    async def get_order_detail(self,exchangeName, id):
        #TODO: MAX下單之後回傳的訊息就包含state, avg_price, executed_volume了 可能不用這個function
        if exchangeName == 'max':
            result = self.registered_exchange['max'].get_private_order_detail(id)
            state = 'closed' if result['state']=='done' else 'rejected'
            return {'state':state ,
                    'avg_price': float(result['avg_price']),
                    'executed_volume': float(result['executed_volume'])}
        else:
            result = await self.registered_exchange[exchangeName].fetch_order(id)
            return {'status': result['status'],
                     'avg_price': result['average'],
                     'executed_volume': result['amount']}


