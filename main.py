from connection_login import XTB
from data_cleanup_plotting import plot_donchain, candles_clean
import json 
from datetime import datetime, timedelta
import yfinance as yf 
import pandas as pd
from dateutil import parser



PASSWORD = "M_aku17@65"
ID = "15397197"
RISK_PER_BUY = 0.07
TAKE_PROFIT_FACTOR = 4

total_profit = 0
profitable_transactions = 0
transactions = 0
tickers = []


def calc_donchain(data):
    temp = data.iloc[:-1]
    data['upper'] = temp['High'].rolling(window = 20).max()
    data['lower'] = temp['Low'].rolling(window = 10).min()
    
    return data

def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    sp500_table = tables[0]
    return sp500_table['Symbol'].tolist()

def get_nasdaq_tickers():
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    tables = pd.read_html(url)
    nasdaq_table = tables[4]
    return nasdaq_table['Ticker'].tolist()

def generate_buy_signal(tickers, start, end):
    count = 0
    buy_singals_list = []

    for symbol in tickers: 

        ticker = yf.Ticker(str(symbol))
        history = ticker.history(interval='1d', start= start, end= end)
        
        if history.empty:
            #print("smth went wrong")
            continue

        history = history.iloc[:-1]

        history = history.reset_index()
        history = calc_donchain(history)
        length = len(history['Close']) - 1

        todays_close = history['Close'].iloc[length]
        donchain_close = history['upper'].iloc[length-1]
        stop_loss = history['lower'].iloc[length-1]
        risk = (todays_close - stop_loss)/todays_close

        #print(history)

        if todays_close > donchain_close and risk < RISK_PER_BUY :
            #print("Buy has been generated")
            buy_signal = {}
            buy_signal['ticker'] = symbol
            buy_signal['opening_price'] = todays_close
            buy_signal['stop_loss'] = stop_loss
            buy_signal['take_profit'] = todays_close + TAKE_PROFIT_FACTOR*(todays_close - stop_loss)
            buy_signal['date'] = history['Date'].iloc[length]
            #buy_signal['no_stocks'] = math.ceil(POSITION_SIZE/todays_close)
            buy_signal['risk'] = risk
            #buy_signal['no_stocks'] = API.calc_position_size(risk, todays_close)


            buy_singals_list.append(buy_signal)


            #print("Difference", todays_close - donchain_close)
            #print(buy_singal)
            count = count + 1
            
    return count, buy_singals_list

def calc_trailing_SL(time_series, opening_price, opening_SL):
    SL = opening_SL
    previous_price = opening_price
    print("Opening price: ", opening_price)
    for i in  time_series:
        print("I", i)
        if i > previous_price:
            SL = SL + (i - opening_price)
            print("SL", SL)
            previous_price = i 
    return SL

def track_profit(tickers, start_day, end_day):
    profit_per_position = {}
    global total_profit, transactions, profitable_transactions

    no_buy_singals, open_positions = generate_buy_signal(tickers, start_day, end_day)
    print("Day", end_day, "No_buy_singals", no_buy_singals)

    for position in open_positions:
        print("Position", position)

        ticker = yf.Ticker(str(position['ticker']))
        old_end_day = end_day
        end_day = end_day + timedelta(60)

        position_history = ticker.history(interval='1d', start= old_end_day, end= end_day)

        if position_history.empty:
            continue

        for index, close_price in enumerate(position_history['Close']):
             
            if close_price < position['stop_loss']:
                profit_per_position[position['ticker']] = (position['stop_loss'] - position['opening_price']) * position['no_stocks']
                break
            elif close_price > position['take_profit']:
                profit_per_position[position['ticker']] = (position['opening_price'] - position['take_profit']) * position['no_stocks']
                break
            else: 
                profit_per_position[position['ticker']] = (close_price - position['opening_price']) * position['no_stocks']
                position['stop_loss'] = calc_trailing_SL(position_history['Close'].iloc[0:index], position['opening_price'], position['stop_loss'])


        if profit_per_position[position['ticker']] > 0:
            profitable_transactions = profitable_transactions + 1
        
        transactions = transactions + 1

    print("Profit per position",profit_per_position)

    for ticker in profit_per_position: 
        total_profit = total_profit + profit_per_position[ticker]

    print("Total profit", total_profit)
    print("Efficiency", profitable_transactions/transactions)

    return profit_per_position


def modify_stop_losses(xtb):

    trades = xtb.get_trades()
    for trade in trades: 
        if trade['cmd'] == 5: 
            old_stop_loss = trade['open_price']
        if trade['cmd'] == 0:
            date_object = parser.parse(trade['open_timeString'])
            candles = xtb.get_candles(trade['symbol'], 1440, date_object)
            candles_unzipped = candles_clean(candles, 100)
            new_stop_loss = calc_trailing_SL(candles_unzipped['Close'], trade['open_price'], old_stop_loss)
            xtb.modify_stop_loss(trade['symbol'], trade['order2'], new_stop_loss)

           




tickers = get_nasdaq_tickers()
#tickers.extend(get_sp500_tickers())
# for i in range(60,70):
#     end_day = start_day + timedelta(i)
#     track_profit(tickers, start_day, end_day)


#tickers = [tick + ".US_9" for tick in tickers]

# PERIOD_D1	  1440	        1440 minutes (1 day)

API = XTB(ID, PASSWORD)

active_signals = []
res = API.get_trades()
for i in res: 
    active_signals.append(i['symbol'])

unique_symbols = set(active_signals)
for symbol in unique_symbols:
    API.check_take_profit(symbol)

today = datetime.now()
start_day = today - timedelta(40)
no_buy_singals, open_positions = generate_buy_signal(tickers, start_day, today)

print("Day", today, "No_buy_singals", no_buy_singals)

for position in open_positions:
    print(position)
    symbol = position['ticker'] + ".US_9"

    volume = API.calc_position_size(position['risk'], position['opening_price'])
    API.open_pkc(symbol, volume, comment=str(round(position['take_profit'],2)))
    API.set_stop_loss(symbol, position['no_stocks'], round(position['stop_loss'],2))


# result = API.get_candles(ticker, period, start)

# df = candles_clean(result, 100000)
# print(df)
# plot_candles(df)

API.logout()