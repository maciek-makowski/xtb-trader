from connection_login import XTB
from data_cleanup_plotting import plot_donchain, candles_clean, plot_candles, plot_imp_areas, plot_MACD
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
import yfinance as yf 
import pandas as pd
#from dateutil import parser
import numpy as np 
# import talib
import math
import time


PASSWORD = "M_aku17@65"
ID = "15397197"
RISK_PER_BUY = 0.1
TAKE_PROFIT_FACTOR = 3

total_profit = 0
profitable_transactions = 0
transactions = 0
#account_size = 10000
tickers = []


def calc_donchain(data):
    temp = data.iloc[:-1]
    data['upper'] = temp['High'].rolling(window = 20).max()
    data['lower'] = temp['Low'].rolling(window = 10).min()
    
    return data
def find_possible_sup_res(data: pd.DataFrame, window_size = 2, deviation = 0.025):
    data['rolling_mean'] = data['Close'].rolling(window = window_size).mean()
    data['lower'] = data['rolling_mean']  * (1 - deviation)
    data['upper'] = data['rolling_mean']  * (1 + deviation)

    data['important_area'] = np.where((data['Low'] < data['lower']) | (data['High'] > data['upper']), data['Close'], np.nan)
    
    return data 

def cluster_values(data, num_clusters):
    clusters = {}
    data = np.array(data).reshape(-1,1)
    kmeans = KMeans(num_clusters)
    kmeans.fit(data)
    labels = kmeans.labels_

    clusters = {i: [] for i in range(num_clusters)}

    for value, label in zip(data, labels):
        clusters[label].append(value)

    for i in labels:
        clusters[i] = np.mean(clusters[i])

    return clusters



def find_polar_change(df, threshold, num_clusters):
    polar_change = []

    for row in df['Low']:
        duration = len(df)
        i = duration - 1

        while i > 0:
            if df['High'].iloc[i] < row:
                #diff = round((row - df['High'].iloc[i])/2 , 5)
                diff = (row - df['High'].iloc[i])/2
                #print("Diff", diff)
                if diff < threshold:
                    #polar = round(row,5) + diff
                    polar = row + diff
                    if polar not in polar_change:
                        polar_change.append(polar)
            i = i - 1
    
    pivots = cluster_values(polar_change, num_clusters)
    polar_change = []
    for x in pivots:
        polar_change.append(pivots[x])
        

    return polar_change

            
            

# def calc_MACD(data: pd.DataFrame):
#     data['MACD'], data['signal'], data['profile'] = talib.MACD(data['Close'])
#     return data


def calc_SL_new3(last_SL, last_price, opening_price):
    SL = last_SL
    if last_price > 1.025 * opening_price:
        if last_SL < opening_price:
            SL = 1.001 * opening_price

            return SL 

        growth = (last_price / opening_price) - 1

        increment = math.ceil((growth / 0.025) - 1) 
        new_SL = SL + (0.025 * increment * opening_price)

        if new_SL > last_SL:
            SL = new_SL

    return SL             
   

def track_profit(tickers, start_day, end_day, active):
    profit_per_position = {}
    global total_profit, transactions, profitable_transactions


    no_buy_singals, open_positions = 1,2
    print("Day", end_day, "No_buy_singals", no_buy_singals)
    print("Active signals", active)

    for position in open_positions:
        
        active.append(position['ticker'])

        print("Position", position)


        ticker = yf.Ticker(str(position['ticker']))
        opening_stop_loss = position['stop_loss']
        old_end_day = end_day
        end_day = end_day + timedelta(240)

        position_history = ticker.history(interval='1d', start= old_end_day, end= end_day)

        if position_history.empty:
            continue

        for index, close_price in enumerate(position_history['Close']):
            #position_history['Low'].iloc[index]
            if  position_history['Low'].iloc[index] < position['stop_loss']:
                profit_per_position[position['ticker']] = (position['stop_loss'] - position['opening_price']) * position['no_stocks']
                print("Closed with SL")
                break
            elif close_price > position['take_profit']:
                profit_per_position[position['ticker']] = (position['take_profit'] - position['opening_price']) * position['no_stocks']
                print("Closed with TP")
                break
            else: 
                profit_per_position[position['ticker']] = (close_price - position['opening_price']) * position['no_stocks']
                #position['stop_loss'] = calc_trailing_SL(position_history['Close'].iloc[0:index], position['opening_price'], opening_stop_loss)
                position['stop_loss'] = calc_SL_new3(position['stop_loss'], position_history['Close'].iloc[index], position['opening_price'])

        if profit_per_position[position['ticker']] > 0:
            profitable_transactions = profitable_transactions + 1
        
        transactions = transactions + 1

    print("Profit per position",profit_per_position)

    for ticker in profit_per_position: 
        total_profit = total_profit + profit_per_position[ticker]

    print("Total profit", total_profit)
    if transactions != 0: print("Efficiency", profitable_transactions/transactions)
    print("Total transactions", transactions)

    return active


        

API = XTB(ID, PASSWORD)

hours = 0
days = 10

start = datetime.now() - timedelta(days, 0,0,0,0,hours)
period = 5 #M5

candles = API.get_candles('EURUSD', period, start)
candles = candles_clean(candles, 100000)
#print(candles)
polars = find_polar_change(candles, 0.000005, 8)
print("POLARS: ", polars)
print("Len", len(polars))
plot_imp_areas(candles, polars)

API.logout()