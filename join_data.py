import sqlite3

# Connect to the databases
conn1 = sqlite3.connect('aggregated.sqlite')
conn2 = sqlite3.connect('visual_crossing.sqlite')
conn3 = sqlite3.connect('labeled.sqlite')

# Create a cursor object
cur1 = conn1.cursor()
cur2 = conn2.cursor()
cur3 = conn3.cursor()

# Create the new table in the new database
cur3.execute("""
    CREATE TABLE weather (
        id INTEGER PRIMARY KEY,
        location TEXT,
        date TEXT,
        time TEXT,
        temperature REAL,
        humidity REAL,
        pressure REAL,
        precipitation REAL,
        precipitation_probability REAL,
        conditions TEXT
    )
""")

# Fetch data from the first database
cur1.execute(
    'SELECT id, location, date, time, temperature, humidity, pressure FROM weather'
)
rows1 = cur1.fetchall()

for row1 in rows1:
    # Fetch the corresponding data from the second database
    cur2.execute(
        """
        SELECT precipitation, precipitation_probability, conditions
        FROM weather
        WHERE date = ? AND time = ?
    """,
        (row1[2], row1[3]),
    )
    row2 = cur2.fetchone()

    if row2 is not None:
        # Combine the data and insert it into the new database
        cur3.execute(
            """
            INSERT INTO weather (
                id, location, date, time, temperature, humidity, pressure,
                precipitation, precipitation_probability, conditions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            row1 + row2,
        )

# Commit the changes and close the connections
conn3.commit()
conn1.close()
conn2.close()
conn3.close()
