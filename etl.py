import yfinance as yf
import pandas as pd 
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
        UPDATE stocks_statements
        SET price = {price}
        WHERE ticker = {ticker} AND date = {date}
    """
    return query

def get_dates_tickers():
    query = f"""
            SELECT ticker, date 
            FROM stock_statements
    """
    return query

def db_execute_query(query_func, read_pandas = False, *args, **kwargs):
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
    query = query_func(*args, **kwargs)
    
    if read_pandas == True: 
        result = pd.read_sql_query(query, conn)
    else:
        print("ELSE")
        cur.execute(query)
        result = cur.fetchall()   

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
        for index in merged_df.index:
            if index.lower() not in db_cols: 
                merged_df = merged_df.drop(index)

        for col_name in merged_df:
            merged_df = merged_df.rename(columns={col_name:col_name.strftime("%Y-%m-%d")})
        
        #print(merged_df)

        for col_name, col_data in merged_df.items():
            for index, data in enumerate(col_data):
                if math.isnan(data):
                    col_data[index] = 0 

            #print(insert_into_query("Stock_statements", tickers[0], col_name, merged_df.index, col_data))
            db_execute_query(insert_into_query, "Stock_statements", x, col_name, merged_df.index, col_data)


if __name__ == "__main__":
   
    tickers_dates = {}
    ticker_dates_prices = db_execute_query(get_dates_tickers, read_pandas=True)
    print(ticker_dates_prices)
 
    
    for index, row in ticker_dates_prices.iterrows():
        temp_ticker = yf.Ticker(row['ticker'])
        end_date = row['date'] + timedelta(120)
        # print(end_date - timedelta(30))
        row['price'] = temp_ticker.history(interval='1d', start= (end_date - timedelta(30)), end= end_date)
    print(ticker_dates_prices)  

        
        

    # for x in tickers: 
    #     print("Ticker", x)
    #     temp_ticker = yf.Ticker(x)

    #     temp_ticker = 

    # db_cols = db_execute_query(get_table_columns)

    # pull_and_insert_to_db(tickers, db_cols)



