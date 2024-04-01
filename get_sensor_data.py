#!/usr/bin/env python3

import os
import sqlite3
from datetime import datetime
from statistics import mean
from time import sleep

import adafruit_bme680
import board
from busio import I2C
from prometheus_client import Gauge, start_http_server

i2c = I2C(board.SCL, board.SDA)
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
# Sea level of Schwäbisch Hall
sensor.sea_level_pressure = 994

script_dir = os.path.dirname(os.path.realpath(__file__))
db_file = os.path.join(script_dir, 'bme680.sqlite')

gh = Gauge('humidity_percent', 'Humidity percentage measured by the Sensor')
gt = Gauge('temperature', 'Temperature measured by the Sensor')
gp = Gauge('pressure', 'Pressure measured by the Sensor')

counter = 0
sensor_data = {'temperature': [], 'humidity': [], 'pressure': []}


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


def read_sensor():
    global counter, sensor_data

    location = 'Schwäbisch Hall'
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')

    if data_exists(location, date, time):
        print('Data already exists in the database.')
        return

    sensor.temperature  # wake up the sensor ;)
    # init. sensor takes some time
    sleep(2)

    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        pressure = sensor.pressure
        sensor_data['temperature'].append(temperature)
        sensor_data['humidity'].append(humidity)
        sensor_data['pressure'].append(pressure)
    except RuntimeError as e:
        print('RuntimeError: {}'.format(e))

    if humidity is not None and temperature is not None and pressure is not None:
        gh.set(humidity)
        gt.set(temperature)
        gp.set(pressure)
        print('Data fetched successfully')
    else:
        print('Failed to fetch data: one or more sensor values are None')

    counter += 1
    if counter > 6:
        mean_temperature = mean(sensor_data['temperature'])
        mean_humidity = mean(sensor_data['humidity'])
        mean_pressure = mean(sensor_data['pressure'])
        save_to_database(
            location, date, time, mean_temperature, mean_humidity, mean_pressure
        )
        sensor_data = {'temperature': [], 'humidity': [], 'pressure': []}
        counter = 0


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
    metrics_port = 9070
    start_http_server(metrics_port)
    print('Serving sensor metrics on :{}'.format(metrics_port))

    while True:
        read_sensor()
        sleep(30)
