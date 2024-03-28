#!/usr/bin/env python3

import os
import sqlite3
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

script_dir = os.path.dirname(os.path.realpath(__file__))
db_file = os.path.join(script_dir, 'visual_crossing.sqlite')


def data_exists(location, date):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT 1 FROM weather WHERE location = ? AND date = ?', (location, date)
        )

        return cursor.fetchone() is not None
    except sqlite3.Error as error:
        print('Data does not exist, proceed. Error:', error)
    finally:
        if conn:
            conn.close()


def fetch_weather_data():
    api_key = os.getenv('VISUAL_CROSSING_API_KEY')
    if not api_key:
        print(
            'No API key found. Please set the VISUAL_CROSSING_API_KEY environment variable.'
        )
        return

    location = 'Heilbronn'
    date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    if data_exists(location, date):
        print('Data already exists in the database.')
        return

    url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/yesterday?unitGroup=metric&maxDistance=30000&include=hours%2Cdays&key={api_key}&contentType=json'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        save_to_database(data)
    except requests.exceptions.RequestException as e:
        print(f'Failed to fetch data: {e}')
    except ValueError as e:
        print(f'Failed to parse JSON response: {e}')


def save_to_database(data):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute(
            'CREATE TABLE IF NOT EXISTS weather (id INTEGER PRIMARY KEY, location text, date text, time text, temperature REAL, humidity REAL, pressure REAL, precipitation REAL, precipitation_probability REAL, conditions text, UNIQUE(location, date, time))'
        )
        day = data['days'][0]
        location = data['address']
        date = day['datetime']
        time = 'Day Overview'
        temperature = day['temp']
        humidity = day['humidity']
        pressure = day['pressure']
        precipitation = day['precip']
        precipitation_probability = day['precipprob']
        conditions = day['conditions']

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
        for hour in day['hours']:
            location = data['address']
            date = day['datetime']
            time = hour['datetime']
            temperature = hour['temp']
            humidity = hour['humidity']
            pressure = hour['pressure']
            precipitation = hour['precip']
            precipitation_probability = hour['precipprob']
            conditions = hour['conditions']

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
    except sqlite3.Error as e:
        print(f'Failed to save data. Error: {e}')
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    fetch_weather_data()
