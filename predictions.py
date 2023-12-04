import tensorflow as tf 
import pandas as pd
import numpy as np
from etl import db_execute_query

def get_data_query():
    query = """
            SELECT * 
            FROM stock_statements; 
    """
    return query

result = db_execute_query(get_data_query, read_pandas=True)

print(result)
print(type(result))