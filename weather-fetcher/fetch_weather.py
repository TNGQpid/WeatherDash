import requests
import psycopg2
import os
from datetime import datetime, timedelta

# Load env manually (Docker handles .env exposure)
API_KEY = os.environ["OWM_API_KEY"]

# Define multiple locations (name, lat, lon)
LOCATIONS = [
    {"name": "Madison", "lat": "43.0731", "lon": "-89.4012"},
    {"name": "Chicago", "lat": "41.8781", "lon": "-87.6298"},
    {"name": "Berlin", "lat": "52.5200", "lon": "13.4050"},
]

# DB config
conn = psycopg2.connect(
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASS"],
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"]
)
cur = conn.cursor()

# Create table if needed
cur.execute("""
CREATE TABLE IF NOT EXISTS weather1 (
    timestamp TIMESTAMP,
    location TEXT,
    temperature REAL,
    feels_like REAL,
    humidity INT,
    pressure INT,
    wind_speed REAL,
    wind_direction INT,
    clouds INT,
    visibility INT,
    description TEXT,
    PRIMARY KEY (timestamp, location)
)
""")

now = datetime.now()

# Fetch and insert for each location
for loc in LOCATIONS:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={loc['lat']}&lon={loc['lon']}&appid={API_KEY}&units=metric"
    )
    r = requests.get(url)
    data = r.json()

    cur.execute("""
        INSERT INTO weather1 (
            timestamp, location, temperature, feels_like,
            humidity, pressure, wind_speed, wind_direction,
            clouds, visibility, description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (timestamp, location) DO NOTHING
    """, (
        now,
        loc["name"],
        data["main"]["temp"],
        data["main"]["feels_like"],
        data["main"]["humidity"],
        data["main"]["pressure"],
        data["wind"]["speed"],
        data["wind"].get("deg"),
        data["clouds"]["all"],
        data.get("visibility"),
        data["weather"][0]["description"]
    ))

# Delete old rows (>5 days)
cutoff = now - timedelta(days=5)
cur.execute("DELETE FROM weather1 WHERE timestamp < %s", (cutoff,))

conn.commit()
cur.close()
conn.close()
