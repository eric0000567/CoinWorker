from datetime import datetime
import asyncio
from PersonalExchangeInfo import PersonalExchangeInfo
from PriceMonitor import PriceMointor
import pandas as pd
import os

arbitrage_dir_path = 'arbitrage_history/'
if not os.path.exists(arbitrage_dir_path):
    os.makedirs(arbitrage_dir_path)

async def bot(person: PersonalExchangeInfo):
    wait_time = 1.66
    start_time = datetime.now()
    priceMointor = PriceMointor()
    earn_times = 0
    print(f"Starting bot: {start_time}")
    message_columns = ['trade_time', 'pair', 'sell_ExName', 'sell_price', 'buy_ExName', 'buy_price', 'order_size', 'earn']
    arbitrage_path = f"{arbitrage_dir_path}/{person.user_name}_{start_time}.csv"
    pd.DataFrame(columns=message_columns).to_csv(arbitrage_path, mode='w')
    
    pairs_and_sizes = [
        (['ETH', 'BTC'], 0.05),
        (['BTC', 'TWD'], 0.003),
        (['ETH', 'TWD'], 0.05),
        (['BTC', 'USDT'], 0.003),
        (['ETH', 'USDT'], 0.05),
        (['USDT', 'TWD'], 90)
    ]
    
    while True:
        try:
            total_time = datetime.now() - start_time
            print('--'*30)
            print(f"Execution time: {total_time}")
            
            trade_signals = [asyncio.ensure_future(priceMointor.trade_signal(pair=pair, min_order_size=size)) for pair, size in pairs_and_sizes]
            
            for trade_signal in asyncio.as_completed(trade_signals):
                result = await trade_signal
                if result is None:
                    continue

                sell_order = asyncio.create_task(person.post_market_order(result['sell']['ex_name'],
                                                        result['pair'],
                                                        'sell',
                                                        result['size'],
                                                        result['sell']['price']))
                buy_order = asyncio.create_task(person.post_market_order(result['buy']['ex_name'],
                                                        result['pair'],
                                                        'buy',
                                                        result['size'],
                                                        result['buy']['price']))
                sell_state = await sell_order
                buy_state = await buy_order

                sell_detail = asyncio.create_task(person.get_order_detail(result['sell']['ex_name'], sell_state['id']))
                buy_detail = asyncio.create_task(person.get_order_detail(result['buy']['ex_name'], buy_state['id']))
                
                sell_result = await sell_detail
                buy_result = await buy_detail

                if sell_result['state'] != 'closed' | buy_result['state'] != 'closed' :
                    raise RuntimeError('Can not get order detail!!')
                
                actual_profit = priceMointor.spread_profit_counter(result['sell']['ex_name'],
                                                            sell_result['avg_price'],
                                                            result['buy']['ex_name'],
                                                            buy_result['avg_price'],
                                                            result['size'])
                pd.DataFrame([datetime.now(),
                              result['pair'],
                              result['sell']['ex_name'],
                              sell_result['avg_price'],
                              result['buy']['ex_name'],
                              buy_result['avg_price'],
                              result['size'],
                              actual_profit
                              ]).to_csv(arbitrage_path,mode='a',header=False)
                earn_times += 1
                print(f"{result['pair'][0]+'/'+result['pair'][1]} sell {result['sell']['ex_name']}:{result['sell']['price']} buy {result['buy']['ex_name']}:{result['sell']['price']} order size: {result['size']} \n earn: {result['pair'][1]}${actual_profit}")
            
            print(f"earn times: {earn_times}")
        except Exception as e:
            print("Exception: ", e)
            await asyncio.gather(priceMointor.close())
            break

        await asyncio.sleep(wait_time)


eric = PersonalExchangeInfo('eric')
asyncio.run(bot(eric))