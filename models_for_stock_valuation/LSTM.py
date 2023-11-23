import pandas as pd
import numpy as np
import tensorflow as tf
from keras.models import Sequential, save_model
from keras.layers import Dense, LSTM
from sklearn.model_selection import train_test_split

df = pd.read_csv('D:/Inne/XTB_api/models_for_stock_valuation/data_assets.csv')
df.set_index('Unnamed: 0', inplace = True)
df = df[df.columns[::-1]]

for index,row in df.iterrows():
    df.loc[index] = df.loc[index].pct_change()

df.dropna(inplace = True, axis = 1)

sequence = np.array(df[['2020', '2021']].values)
estimated_value = np.array(df['2022'].values)

print(sequence.shape)
print(estimated_value.shape)

sequence_train, sequence_test, value_train, value_test = train_test_split(sequence, estimated_value, test_size = 0.1, random_state = 42)

model = Sequential()
model.add(LSTM(2, input_shape = (2,1)))

model.compile(
    loss = 'mse',
    optimizer = 'adam',
    metrics = ['mae']
)

model.fit(sequence_train, value_train, validation_data =(sequence_test, value_test), epochs = 1)
prediction = model.predict(sequence[0])
print(prediction, estimated_value[0])