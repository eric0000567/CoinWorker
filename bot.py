from datetime import datetime, timedelta
import asyncio
from PersonalExchangeInfo import PersonalExchangeInfo
from PriceMonitor import PriceMointor
import pandas as pd
import os
from message_control import send_email

#TODO 新增介面系統，做個網頁出來讓自己好觀察
priceMointor = PriceMointor()
eric = PersonalExchangeInfo('eric')
pairs_and_sizes = [
        (['ETH', 'BTC'], 0.05),
        (['BTC', 'TWD'], 0.003),
        (['ETH', 'TWD'], 0.05),
        (['BTC', 'USDT'], 0.003),
        (['ETH', 'USDT'], 0.05),
        (['USDT', 'TWD'], 90)
    ]

currency_set = set()
for pair, _ in pairs_and_sizes:
    currency_set.update(pair)

unique_currencies = list(currency_set)

arbitrage_dir_path = 'arbitrage_history/'
if not os.path.exists(arbitrage_dir_path):
    os.makedirs(arbitrage_dir_path)


async def init_balance(init_invest_amount=300000, base_currency='TWD', unique_currencies_num=4):
    usdt_price = await priceMointor.fetch_max_order_book('USDT',base_currency)
    eth_price = await priceMointor.fetch_max_order_book('ETH',base_currency)
    btc_price = await priceMointor.fetch_max_order_book('BTC',base_currency)

    per_exchange_money = init_invest_amount / len(priceMointor.exchanges_name)
    per_pair_money = per_exchange_money / unique_currencies_num

    currencies_price = {'USDT':usdt_price['asks'][0][0],
                        'ETH':eth_price['asks'][0][0],
                        'BTC':btc_price['asks'][0][0],
                        base_currency:1}
    # TODO 要獲取每間交易所初始的幣有多少
    per_pair_amount = {coin_name: float(per_pair_money/float(currencies_price[coin_name])) for coin_name in currencies_price}
    per_exchange_amount = {name: per_pair_amount for name in priceMointor.exchanges_name}
    return pd.DataFrame.from_dict(per_exchange_amount, orient='index')

async def rebalance_fee(init_invest_money, trade_df: pd.DataFrame):
    init_invest = pd.DataFrame(init_invest_money)
    benchmark_values = pd.DataFrame(init_invest_money)
    rebalance_times = 0
    for row in trade_df.itertuples():
        init_invest[row.sell_ExName][eval(row.pair)[0]] -= float(row.order_size)
        # init_invest[row.sell_ExName][eval(row.pair)[1]] += float(row.order_size)*float(row.sell_price)

        # init_invest[row.buy_ExName][eval(row.pair)[0]] += float(row.order_size)
        init_invest[row.buy_ExName][eval(row.pair)[1]] -= float(row.order_size)*float(row.buy_price)
        below_20_percent = init_invest < (benchmark_values*0.2)
        init_invest[below_20_percent] = benchmark_values
        rebalance_times += below_20_percent.sum().sum()
    return rebalance_times


async def bot(person: PersonalExchangeInfo):
    frequency = 3
    start_time = datetime.now()
    next_send_time = start_time + timedelta(hours=6)
    earn_times = 0
    init_money = 300000
    person_init_balance = await init_balance(init_money,"TWD",len(unique_currencies))
    print(person_init_balance)
    print(f"Starting bot: {start_time}")
    message_columns = ['trade_time', 'pair', 'sell_ExName', 'sell_price', 'bids_order', 'buy_ExName', 'buy_price', 'asks_order', 'order_size', 'earn', 'base_currency']
    arbitrage_path = f"{arbitrage_dir_path}/{person.user_name}_{start_time}.csv"
    pd.DataFrame(columns=message_columns).to_csv(arbitrage_path, mode='w',index=False)
    await send_email(f"arbitrage bot start at {start_time}",
    f"每{frequency}秒監測數據一次，以下為監測的交易對及掛單數量\n{pairs_and_sizes}\n需要提供{unique_currencies}這些幣種\n初始投資金額為：{init_money}\n目前投資的交易所：{priceMointor.exchanges_name}\n每個交易所及交易對的數量為：{person_init_balance}",[])
  
    while True:
        try:
            total_time = datetime.now() - start_time            
            trade_signals = [asyncio.ensure_future(priceMointor.trade_signal(pair=pair, min_order_size=size)) for pair, size in pairs_and_sizes]
            
            for trade_signal in asyncio.as_completed(trade_signals):
                result = await trade_signal
                if result is None:
                    continue
                #以下為測試時使用-------
                actual_profit = priceMointor.spread_profit_counter(result['sell']['ex_name'],
                                                            result['sell']['price'],
                                                            result['buy']['ex_name'],
                                                            result['buy']['price'],
                                                            result['size'])
                                                            
                if person_init_balance[result['pair'][0]].loc[result['sell']['ex_name']] < result['size'] or \
                    person_init_balance[result['pair'][1]].loc[result['buy']['ex_name']] < result['size']* result['buy']['price']:
                    print(f"餘額不足無法進行搬磚\n{result['sell']['ex_name']}的{result['pair'][0]}餘額剩餘: {person_init_balance[result['pair'][0]].loc[result['sell']['ex_name']]}\n{result['buy']['ex_name']}的{result['pair'][1]}餘額剩餘: {person_init_balance[result['pair'][1]].loc[result['buy']['ex_name']]}\n 此次需要sell {result['pair'][0]}: {result['size']}\n 需要buy {result['pair'][1]}: {result['size'] * result['buy']['price']}\n")
                    continue

                person_init_balance[result['pair'][0]].loc[result['sell']['ex_name']] -= result['size']
                person_init_balance[result['pair'][1]].loc[result['sell']['ex_name']] += (result['size'] * result['sell']['price'])

                person_init_balance[result['pair'][1]].loc[result['buy']['ex_name']] -= (result['size'] * result['buy']['price'])
                person_init_balance[result['pair'][0]].loc[result['buy']['ex_name']] += result['size']
                print(person_init_balance)

                profit_report = pd.DataFrame([[datetime.now(),
                              result['pair'],
                              result['sell']['ex_name'],
                              result['sell']['price'],
                              result['sell']['order_size'],
                              result['buy']['ex_name'],
                              result['buy']['price'],
                              result['buy']['order_size'],
                              result['size'],
                              actual_profit,
                              result['pair'][1]
                              ]])
                profit_report.to_csv(arbitrage_path,mode='a',header=False,index=False)
                earn_times += 1
                if datetime.now() >= (next_send_time+timedelta(hours=4)):
                    df = pd.read_csv(arbitrage_path)
                    df_no_duplicates = df.drop_duplicates(subset=['sell_price','buy_price', 'bids_order','asks_order'])

                    df_no_duplicates.to_csv(f'{arbitrage_dir_path}/earn_history.csv',index=False)
                    # rebalance_times = await rebalance_fee(person_init_balance, df_no_duplicates)
                    twd_earn = df_no_duplicates[df_no_duplicates['base_currency'] == 'TWD']['earn'].sum()
                    usdt_earn = df_no_duplicates[df_no_duplicates['base_currency'] == 'USDT']['earn'].sum()
                    btc_earn = df_no_duplicates[df_no_duplicates['base_currency'] == 'BTC']['earn'].sum()

                    await send_email(f"arbitrage earn {len(df_no_duplicates['sell_price'])} times",f"總運行時間：{total_time} \n\nTWD總獲利：{twd_earn}\nUSDT總獲利：{usdt_earn}\nBTC總獲利：{btc_earn}\n\n獲利明細請看附件\n\n個人餘額剩餘: {person_init_balance}",[f'{arbitrage_dir_path}/earn_history.csv','output.log'])
                    next_send_time = datetime.now()
                    print(f"Execution time: {total_time}")
                    print('--'*30)

                continue
                #以上為測試時使用-------
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
                                                            result['size'],
                                                            result['pair'][1])
                pd.DataFrame([[datetime.now(),
                              result['pair'],
                              result['sell']['ex_name'],
                              sell_result['avg_price'],
                              result['sell']['order_size'],
                              result['buy']['ex_name'],
                              buy_result['avg_price'],
                              result['buy']['order_size'],
                              result['size'],
                              actual_profit,
                              result['pair'][1]
                              ]]).to_csv(arbitrage_path,mode='a',header=False,index=False)
                earn_times += 1
                print(f"{result['pair'][0]+'/'+result['pair'][1]} sell {result['sell']['ex_name']}:{result['sell']['price']} buy {result['buy']['ex_name']}:{result['sell']['price']} order size: {result['size']} \n earn: {result['pair'][1]}${actual_profit}")
            
            # print(f"earn times: {earn_times}")
        except Exception as e:
            #TODO:錯誤不中止，進行檢查餘額及訊息搜集
            print("Exception: ", e)
            # await asyncio.gather(priceMointor.close())
            await send_email(f"Arbitrage Exception {e}",f"{e}",['error.log'])
            await asyncio.sleep(30)


        await asyncio.sleep(frequency)



asyncio.run(bot(eric))




# async def balance_monitor(base_currency='TWD'):
    # exchanges_balance = {name:await eric.get_balance(name, unique_currencies) for name in priceMointor.exchanges_name}
    # usdt_price = await priceMointor.fetch_max_order_book('USDT',base_currency)
    # eth_price = await priceMointor.fetch_max_order_book('ETH',base_currency)
    # btc_price = await priceMointor.fetch_max_order_book('BTC',base_currency)

    # currencies_price = {'USDT':usdt_price['asks'][0][0],
    #                     'ETH':eth_price['asks'][0][0],
    #                     'BTC':btc_price['asks'][0][0],}
    # # TODO 要獲取每間交易所初始的幣有多少
    # per_pair_amount = {coin_name: per_pair_money/float(currencies_price[coin_name]) for coin_name in currencies_price}
    # print(exchanges_balance)
    # print(currencies_price)
    # print(per_pair_amount)

# asyncio.run(bot(eric))
