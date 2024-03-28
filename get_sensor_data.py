#!/usr/bin/env python3

import os
import sqlite3
from datetime import datetime

import adafruit_bme680
import board
from busio import I2C

#sensor = adafruit_bme680.BME680_(board.I2C())
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
#Sea level of Schwäbisch Hall
sensor.sea_level_pressure = 304

script_dir = os.path.dirname(os.path.realpath(__file__))
db_file = os.path.join(script_dir, 'bme680.sqlite')


def data_exists(location, date, time):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT 1 FROM weather WHERE location = ? AND date = ? AND time = ?',
            (location, date, time),
        )

        return cursor.fetchone() is not None
    except sqlite3.Error as error:
        print('Data does not exist, proceed. Error:', error)
    finally:
        if conn:
            conn.close()


def fetch_sensor_data():
    location = 'Heilbronn'
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S')

    if data_exists(location, date, time):
        print('Data already exists in the database.')
        return

    temperature = sensor.temperature
    humidity = sensor.humidity
    pressure = sensor.pressure

    if temperature is None or humidity is None or pressure is None:
        print('Failed to fetch data: one or more sensor values are None')
    else:
        print('Data fetched successfully')

    save_to_database(location, date, time, temperature, humidity, pressure)


def save_to_database(location, date, time, temperature, humidity, pressure):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute(
            'CREATE TABLE IF NOT EXISTS weather (id INTEGER PRIMARY KEY, location text, date text, time text, temperature REAL, humidity REAL, pressure REAL, precipitation REAL, precipitation_probability REAL, conditions text, UNIQUE(location, date, time))'
        )

        precipitation = None
        precipitation_probability = None
        conditions = None

        cursor.execute(
            'INSERT OR IGNORE INTO weather (location, date, time, temperature, humidity, pressure, precipitation, precipitation_probability, conditions) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                location,
                date,
                time,
                temperature,
                humidity,
                pressure,
                precipitation,
                precipitation_probability,
                conditions,
            ),
        )

        if cursor.rowcount == 0:
            print(
                'Data for this date and location already exists in the database, insert operation ignored.'
            )
        else:
            print('Data saved successfully')

        conn.commit()
    except sqlite3.Error as error:
        print('Failed to save data:', error)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    fetch_sensor_data()
