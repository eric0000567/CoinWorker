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
    
    async def post_order(self, exchangeName, size, price, side):
        #TODO:新增異步下單及檢測該單實際價值(分成post buy & post sell可能比較好)
        if exchangeName == 'max':
            self.registered_exchange['max']
        else:
            self.registered_exchange[exchangeName]
        pass
