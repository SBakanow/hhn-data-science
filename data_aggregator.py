import os
import sqlite3

import pandas as pd

script_dir = os.path.dirname(os.path.realpath(__file__))
db_file = os.path.join(script_dir, 'bme680.sqlite')

with sqlite3.connect(db_file) as conn:
    df = pd.read_sql_query('SELECT * FROM weather', conn)

df = df.drop(columns=['id'])

df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
df.set_index('datetime', inplace=True)

df_resampled = df.select_dtypes(include=['float64', 'int']).resample('h').mean()
df_resampled.reset_index(inplace=True)

df_resampled['date'] = df_resampled['datetime'].dt.date
df_resampled['time'] = df_resampled['datetime'].dt.strftime('%H:%M:%S')

df_resampled = df_resampled.drop(columns=['datetime']).assign(
    id=lambda _: _.index + 1,
    location='Schwäbisch Hall',
    precipitation=None,
    precipitation_probability=None,
    conditions=None,
)

df_resampled = df_resampled.round({'temperature': 1, 'humidity': 1, 'pressure': 1})

df_resampled = df_resampled[
    [
        'id',
        'location',
        'date',
        'time',
        'temperature',
        'humidity',
        'pressure',
        'precipitation',
        'precipitation_probability',
        'conditions',
    ]
]

with sqlite3.connect('aggregated.sqlite') as new_conn:
    df_resampled.to_sql('weather', new_conn, if_exists='replace', index=False)
