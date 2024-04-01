#!/usr/bin/env python3

import os
import sqlite3
from datetime import datetime

import time as timee
import board
from busio import I2C
import adafruit_bme680

from prometheus_client import Gauge, start_http_server

i2c = I2C(board.SCL, board.SDA)
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
#Sea level of Schwäbisch Hall
sensor.sea_level_pressure = 994

script_dir = os.path.dirname(os.path.realpath(__file__))
db_file = os.path.join(script_dir, 'bme680.sqlite')

gh = Gauge('umiditypercent',
           'Humidity percentage measured by the Sensor')
gt = Gauge('temperature',
           'Temperature measured by the Sensor', ['scale'])
           
gt.labels('celsius')
gt.labels('fahrenheit')

def celsius_to_fahrenheit(degrees_celsius):
        return (degrees_celsius * 9/5) + 32

#Function to read sensor data and format for Prometheus
def read_sensor():
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        #pressure = sensor.pressure
    except RuntimeError as e:
        # GPIO access may require sudo permissions
        # Other RuntimeError exceptions may occur, but
        # are common.  Just try again.
        print("RuntimeError: {}".format(e))

    if humidity is not None and temperature is not None:
        gh.set(humidity)
        gt.labels('celsius').set(temperature)
        gt.labels('fahrenheit').set(celsius_to_fahrenheit(temperature))

        #log.info("Temp:{0:0.1f}*C, Humidity: {1:0.1f}%".format(temperature, humidity))

    timee.sleep(10)

if __name__ == "__main__":
    # Expose metrics
    metrics_port = 9070
    start_http_server(metrics_port)
    print("Serving sensor metrics on :{}".format(metrics_port))
    #log.info("Serving sensor metrics on :{}".format(metrics_port))

    while True:
        read_sensor()
