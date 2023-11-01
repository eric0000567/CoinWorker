from datetime import datetime
import asyncio
from PersonalExchangeInfo import PersonalExchangeInfo
from PriceMonitor import PriceMointor
import pandas as pd
import os

arbitrage_path = 'arbitrage_history/'
if not os.path.exists(arbitrage_path):
    os.makedirs(arbitrage_path)

async def main():
    wait_time = 1.66
    start_time = datetime.now()
    eric = PersonalExchangeInfo('eric')
    eric_mointor = PriceMointor(eric)
    earn_times = 0
    print("Starting bot")
    message_columns = ['time', 'pair', 'sell_price', 'buy_price', 'order_size', 'earn']
    pd.DataFrame(columns=message_columns).to_csv(f"{arbitrage_path}/{eric.user_name}_{start_time}.csv", mode='w')
    while True:
        try:
            total_time = datetime.now() - start_time
            print(f"running time: {total_time}")
            PriceMointors = [asyncio.ensure_future(eric_mointor.bot(pair=['ETH','BTC'], min_order_size=0.05)),
                            asyncio.ensure_future(eric_mointor.bot(pair=['BTC','TWD'],min_order_size=0.001)),
                            asyncio.ensure_future(eric_mointor.bot(pair=['ETH','TWD'],min_order_size=0.05)),
                            asyncio.ensure_future(eric_mointor.bot(pair=['BTC','USDT'],min_order_size=0.001)),
                            asyncio.ensure_future(eric_mointor.bot(pair=['ETH','USDT'],min_order_size=0.05)),
                            asyncio.ensure_future(eric_mointor.bot(pair=['USDT','TWD'],min_order_size=0.05))]
            results = await asyncio.gather(*PriceMointors)
            for result in results:
                if result is not None:
                    result.to_csv(f"{arbitrage_path}/{eric.user_name}_{start_time}.csv", mode='a',header=False)
                    earn_times += 1
            print(f"earn times: {earn_times}")
            print('--'*30)
        except Exception as e:
            print("Exception: ", e)
            await asyncio.gather(eric_mointor.close())

        await asyncio.sleep(wait_time)

asyncio.run(main())