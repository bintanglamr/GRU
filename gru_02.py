# -*- coding: utf-8 -*-
"""GRU 02.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/166SgbmbS4cZWWIoByTTuY6hp6VnEH4Ic

# IMPORT LIBRARIES
"""

import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams["figure.figsize"] = (12,5)
import warnings
warnings.filterwarnings('ignore')
from sklearn.metrics import mean_squared_error, explained_variance_score, max_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

"""# LOAD DATA"""

# Import the CSV file
df = pd.read_csv("/content/busan_dataset.csv")

df.head()

# remove spaces on the column
df.columns = df.columns.str.lstrip()
df.columns = df.columns.str.rstrip()

# Parse the "Date" column
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

"""# Data Exploration"""

df.shape

df.info()

df.head()

df.describe()

"""# Data Cleaning"""

df.isna().sum()

# fill the nan values by upper row value
df = df.fillna(method='ffill')
df.tail()

"""# Data Engineering"""

# Extracting features from the index before filtering the DataFrame
df['hour'] = df.index.hour
df['day_of_month'] = df.index.day
df['day_of_week'] = df.index.dayofweek
df['month'] = df.index.month

# Now filter the DataFrame to include only the required columns and the new features
required_cols = ['GHI_Average', 'SunZenith_KMU', 'Ambient_Pressure', 'Water', 'AOD', 'wv_500', 'CI_Beyer', 'hour', 'day_of_month', 'day_of_week', 'month']
df = df[required_cols]

# Display the first few rows to confirm the columns are present
print(df.head())

"""# Data Exploration #2"""

sns.lineplot(x=df.index, y='GHI_Average', data=df)
plt.show()

df_by_month = df.resample('M').sum()
sns.lineplot(x=df_by_month.index, y='GHI_Average', data=df_by_month)
plt.show()

# Check the list of column names in the DataFrame
print(df.columns)

# Create a figure with 4 subplots (2 rows, 2 columns)
fig, axs = plt.subplots(2, 2, figsize=(18, 6))

# Ensure that axs is a flat array, in case it isn't already
if isinstance(axs, np.ndarray):
    axs = axs.flatten()

# Plot 1: Hourly GHI Average
sns.pointplot(x='hour', y='GHI_Average', data=df, ax=axs[0])
axs[0].set_title('Hourly GHI Average')

# Plot 2: GHI Average by Day of the Week
sns.pointplot(x='day_of_week', y='GHI_Average', data=df, ax=axs[1])
axs[1].set_title('GHI Average by Day of the Week')

# Plot 3: GHI Average by Day of the Month
sns.pointplot(x='day_of_month', y='GHI_Average', data=df, ax=axs[2])
axs[2].set_title('GHI Average by Day of the Month')

# Plot 4: GHI Average by Month
sns.pointplot(x='month', y='GHI_Average', data=df, ax=axs[3])
axs[3].set_title('GHI Average by Month')

# Show the plots
plt.tight_layout()
plt.show()

"""# Data Preprocessing"""

# Train & Test Datasest split
train_size = int(len(df) * 0.9)
test_size = len(df) - train_size
train, test = df.iloc[0:train_size], df.iloc[train_size:len(df)]
print('Train size:',len(train))
print('Test size:', len(test))

cols = ['SunZenith_KMU','Ambient_Pressure','Water','AOD','wv_500','CI_Beyer']

scaler = RobustScaler()
scaler = scaler.fit(np.asarray(train[cols]))

train.loc[:, cols] = scaler.transform(np.asarray(train[cols]))
test.loc[:, cols] = scaler.transform(np.asarray(test[cols]))

# scaling GHI
GHI_scaler = RobustScaler()
GHI_scaler = GHI_scaler.fit(train[['GHI_Average']])
train['GHI_Average'] = GHI_scaler.transform(train[['GHI_Average']])
test['GHI_Average'] = GHI_scaler.transform(test[['GHI_Average']])

print('Train shape:',train.shape)
print('Test shape:', test.shape)

"""# Model Building"""

def create_dataset(X, y, time_steps=1):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        v = X.iloc[i:(i + time_steps)].values
        Xs.append(v)
        ys.append(y.iloc[i + time_steps])
    return np.array(Xs), np.array(ys)

time_steps = 10
# reshape to [samples, time_steps, features]
X_train, y_train = create_dataset(train, train.GHI_Average, time_steps)
X_test, y_test = create_dataset(test, test.GHI_Average, time_steps)
print(X_train.shape, y_train.shape)

"""# **GRU**"""

# GRU model design

gru_model = tf.keras.Sequential()
gru_model.add(tf.keras.layers.GRU(units=128, input_shape=(X_train.shape[1], X_train.shape[2])))
gru_model.add(tf.keras.layers.Dropout(rate=0.2))
gru_model.add(tf.keras.layers.Dense(units=1))
gru_model.compile(loss='mean_squared_error', optimizer='adam')
gru_model.summary()

gru_history = gru_model.fit(X_train, y_train,epochs=50,batch_size=32,validation_split=0.1,shuffle=False)

# history plotting
plt.plot(gru_history.history['loss'], label='train')
plt.plot(gru_history.history['val_loss'], label='validation')
plt.legend()
plt.show()

# inverse scaling

y_pred = gru_model.predict(X_test)
y_train_inv = GHI_scaler.inverse_transform(y_train.reshape(1, -1))
y_test_inv = GHI_scaler.inverse_transform(y_test.reshape(1, -1))
y_pred_inv = GHI_scaler.inverse_transform(y_pred)

# visualizing predicition
plt.plot(y_test_inv.flatten(), marker='.', label='true')
plt.plot(y_pred_inv.flatten(), 'r', label='predicted')
plt.legend()
plt.show()

gru_train_pred = gru_model.predict(X_train)
gru_test_pred = gru_model.predict(X_test)
print('Train RMSE:', np.sqrt(mean_squared_error(y_train, gru_train_pred)))
print('Test RMSE:', np.sqrt(mean_squared_error(y_test, gru_test_pred)))
print('MSE:', mean_squared_error(y_test, y_pred))
print('Explained variance score:', explained_variance_score(y_test, y_pred))
print('Max error:', max_error(y_test, y_pred))

from sklearn.metrics import mean_squared_error
import numpy as np
# Compute RMSE
rmse = np.sqrt(mean_squared_error(y_test_inv.flatten(), y_pred_inv.flatten()))
print('Test RMSE: %.3f' % rmse)

#evaluation metrics
from sklearn.metrics import mean_squared_error
from math import sqrt
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error

# Compute Metrics
r2 = r2_score(y_test_inv.flatten(), y_pred_inv.flatten())
print('R^2:', r2)

mae = mean_absolute_error(y_test_inv.flatten(), y_pred_inv.flatten())
print('MAE:', mae)

mse = mean_squared_error(y_test_inv.flatten(), y_pred_inv.flatten())
print('MSE:', mse)

rmse = np.sqrt(mean_squared_error(y_test_inv.flatten(), y_pred_inv.flatten()))
print('RMSE: %.3f' % rmse)

mbe = np.mean(diff)
print('MBE:', mbe)

rrmse = np.sqrt(mean_squared_error(y_test_inv.flatten(), y_pred_inv.flatten())) / np.mean(y_test_inv.flatten())
print('RRMSE:', rrmse)

rmbe = mbe / np.mean(y_test_inv.flatten())
print('RMBE:', rmbe)

# Create dictionary and DataFrame
metrics = {
    'Metric': ['R^2', 'MAE', 'MSE', 'RMSE', 'MBE', 'RRMSE', 'RMBE'],
    'Value': [r2, mae, mse, rmse, mbe, rrmse, rmbe]
}
df_metrics = pd.DataFrame(metrics)

# Display the DataFrame
df_metrics.head()

# Assuming 'df' has a DateTime index and you want to keep the corresponding dates for the test set
dates = df.index[train_size + time_steps:].to_list()

# Combine the predicted and actual values with the dates
results_df = pd.DataFrame({
    'Time': dates,
    'Actual GHI': y_test_inv.flatten(),
    'Predicted GHI': y_pred_inv.flatten()
})

# Display the first few rows
results_df.head()

# Save the table to a CSV file
results_df.to_csv('GRU_GHI_predictions.csv', index=False)

# Save the table to an Excel file
results_df.to_excel('GRU02_GHI_predictions.xlsx', index=False)