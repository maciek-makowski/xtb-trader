import plotly.graph_objects as go
import plotly.express as px 
import pandas as pd

def candles_clean(zipped_list, lot_size):
    df = pd.DataFrame(zipped_list, columns = ['Date','Open','Close','High','Low'])
    df['Close'] = (df['Open'] + df['Close'])/lot_size
    df['High'] = (df['Open'] + df['High'])/lot_size
    df['Low'] = (df['Open'] + df['Low'])/lot_size
    df['Open'] = df['Open']/lot_size
    return df



def plot_candles(df, ma = 0):
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])
                ])
    if ma != 0:
        print("ELO")

    fig.show()


def plot_donchain(df):
    candlestick = go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])
    line_up = go.Scatter(x=df['Date'], y =df['upper'], mode ='lines')
    line_low = go.Scatter(x=df['Date'], y =df['lower'], mode ='lines')

    fig = go.Figure(data = [candlestick, line_up, line_low])
    fig.show()