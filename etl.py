import yfinance as yf
import pandas as pd 
import numpy as np
import math
import psycopg2
from datetime import datetime, timedelta
from main import get_nasdaq_tickers, get_sp500_tickers

def create_table_query(table_name, column_names):
    return f"CREATE TABLE {table_name} (id SERIAL PRIMARY KEY, Ticker varchar(5) NOT NULL, Date date, {', '.join([f'{col} float' for col in column_names])});"

def add_columns_query(table_name, column_names):
    query = f"""
        ALTER TABLE {table_name}
        {', '.join([f'ADD COLUMN {col} float' for col in column_names])};
    """
    return query

def insert_into_query(table_name,ticker, date, columns, data):
    query = f"""
    INSERT INTO {table_name} (ticker, date, {', '.join([f'{col}' for col in columns])})
    VALUES ('{ticker}', '{date}', {', '.join([f'{i}' for i in data])}) RETURNING id;
    
"""
    return query

def update_price_query(price, ticker, date):
    query = f"""
        UPDATE stock_statements
        SET price = {price}
        WHERE ticker = '{ticker}' AND date = '{date}';
    """
    return query

def get_dates_tickers():
    query = f"""
            SELECT ticker, date 
            FROM stock_statements
    """
    return query

def db_execute_query(query_func, *args, read = False, read_pandas = False):
    db_name = "stocks_data"
    user = "stocks"
    password = "1234"
    host = "localhost"
    port = "5432"  # Default PostgreSQL port

    # Create a connection to the PostgreSQL server
    conn = psycopg2.connect(
        dbname=db_name,
        user=user,
        password=password,
        host=host,
        port=port
    )

    # Create a cursor object to execute SQL queries
    cur = conn.cursor()

    # Create a table with the specified columns
    query = query_func(*args)

    if read == True: 
        if read_pandas == True: 
            result = pd.read_sql_query(query, conn)
        else:
            cur.execute(query)
            result = cur.fetchall()  
    else : 
        cur.execute(query) 
        result = "Write query"

    # Commit the changes to the database
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()

    return result

def get_table_columns():
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'stock_statements';
    
    """
    return query 

def pull_and_insert_to_db(tickers, db_cols):
    #indexes_to_drop = ["RentExpenseSupplemental", "DilutedAverageShares", "DilutedEPS", "DilutedNIAvailtoComStockholders", "RentAndLandingFees", "OtherIncomeExpense", "RestructuringAndMergernAcquisition", "DepreciationAmortizationDepletionIncomeStatement", "Amortization", "AmortizationOfIntangiblesIncomeStatement"] 
    
    to_del = [0,1,2]
    db_cols = np.delete(db_cols, to_del)

    for x in tickers: 
        print("Ticker", x)
        temp_ticker = yf.Ticker(x)
        result = temp_ticker.get_income_stmt()
        result = result.T
        result_1 = temp_ticker.get_balance_sheet().T
        result_2 = temp_ticker.get_cash_flow().T

        merged_df = pd.merge(result, result_1, left_index=True, right_index=True, how='left')
        merged_df = pd.merge(merged_df, result_2, left_index=True, right_index=True, how='left').T
        #merged_df = merged_df.drop(indexes_to_drop)
        merged_df.index = merged_df.index.str.lower()

        for index in merged_df.index:
            if index.lower() not in db_cols: 
                merged_df = merged_df.drop(index)
            
        for db_col in db_cols: 
            if db_col not in merged_df.index: 
                for col in merged_df:
                    merged_df[col][db_col] = 0

        for col_name in merged_df:
            merged_df = merged_df.rename(columns={col_name:col_name.strftime("%Y-%m-%d")})
        
        #print("MDF ", merged_df)

        for col_name, col_data in merged_df.items():
            for index, data in enumerate(col_data):
                if math.isnan(data):
                    col_data[index] = 0 

            #print(insert_into_query("Stock_statements", tickers[0], col_name, merged_df.index, col_data))
            db_execute_query(insert_into_query, "Stock_statements", x, col_name, merged_df.index, col_data)

def calc_trading_day(start_day: datetime, period):
    end_day = start_day + timedelta(period)
    if end_day > datetime.now().date():
        return datetime.today()
    if 1 <= end_day.weekday() <= 4:
        return end_day 
    else: 
        while not 1<= end_day.weekday() <= 4:
            end_day = end_day + timedelta(1)
    return end_day 
    


if __name__ == "__main__":
   
    tickers_dates = {}
    ticker_dates_prices = db_execute_query(get_dates_tickers,read = True, read_pandas=True)
    prices = []
    print(ticker_dates_prices)
    
    for index, row in ticker_dates_prices.iterrows():
        temp_ticker = yf.Ticker(row['ticker'])
        period = 90
        end_date = calc_trading_day(row['date'], period)
        price = temp_ticker.history(interval='1d', start= (end_date - timedelta(1)), end= end_date)
        while price.empty:
            print("If entered")
            period = period + 1
            end_date = calc_trading_day(row['date'], period)

            print("End date", end_date)

            my_datetime = datetime.combine(end_date, datetime.min.time())
        
            price = temp_ticker.history(interval='1d', start= (end_date - timedelta(1)), end= end_date)

        prices.append(price['Close'].iloc[0])

    ticker_dates_prices = ticker_dates_prices.assign(new_col = prices)
    ticker_dates_prices = ticker_dates_prices.rename(columns={"new_col":"price"})

    print(ticker_dates_prices)  

    for _, row in ticker_dates_prices.iterrows():
        print("Price", row['price'], "Ticker", row['ticker'], "Date", row['date'])
        db_execute_query(update_price_query, row['price'], row['ticker'], row['date'])

        
 
    ############ UPLOADING ALL OF THE RECORDS TO THE DB ##########################################################   
    # tickers = get_sp500_tickers()

    # db_cols = db_execute_query(get_table_columns, read = True, read_pandas = True)
    

    # pull_and_insert_to_db(tickers, db_cols['column_name'].values)



