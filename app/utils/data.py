import os
import random
import psycopg2
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# DATABASE_URL should be like:
# postgresql://username:password@dpg-xxxx.ap-south-1.postgres.render.com:5432/groundwater_db_cbkf
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env file")

# Connect to Render PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# --- Insert helper functions ---
def get_state_id(state_name):
    cur.execute("SELECT state_id FROM states WHERE state_name = %s", (state_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO states (state_name) VALUES (%s) RETURNING state_id", (state_name,))
    return cur.fetchone()[0]

def get_city_id(city_name, state_id):
    cur.execute("SELECT city_id FROM cities WHERE city_name = %s", (city_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO cities (city_name, state_id) VALUES (%s, %s) RETURNING city_id",
        (city_name, state_id),
    )
    return cur.fetchone()[0]

def get_parameter_id(param_name, unit):
    cur.execute("SELECT parameter_id FROM parameters WHERE parameter_name = %s", (param_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO parameters (parameter_name, unit) VALUES (%s, %s) RETURNING parameter_id",
        (param_name, unit),
    )
    return cur.fetchone()[0]

# --- Prepare static values ---
state_name = "Uttar Pradesh"
cities = ["Ayodhya", "Sonbhadra", "Mirzapur"]
parameters = [
    ("Groundwater Level", "m"),
    ("Water Recharged", "bcm"),
    ("Rainfall", "mm"),
    ("Exploitation", "%"),
]

# --- Insert states, cities, parameters ---
state_id = get_state_id(state_name)
city_ids = [get_city_id(city, state_id) for city in cities]
param_ids = {p[0]: get_parameter_id(p[0], p[1]) for p in parameters}

# --- Generate dummy yearly data ---
years = range(2000, 2025)

for city_id in city_ids:
    for year in years:
        for pname, unit in parameters:
            pid = param_ids[pname]
            # Generate realistic dummy values
            if pname == "Groundwater Level":
                value = round(random.uniform(200, 400), 2)  # meters
            elif pname == "Water Recharged":
                value = round(random.uniform(10, 100), 2)   # bcm
            elif pname == "Rainfall":
                value = round(random.uniform(100, 1000), 2) # mm
            elif pname == "Exploitation":
                value = round(random.uniform(20, 120), 2)   # %
            else:
                value = round(random.uniform(1, 500), 2)

            cur.execute(
                """
                INSERT INTO yearly_data (city_id, parameter_id, year, value)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (city_id, pid, year, value),
            )



                    


# Commit and close
conn.commit()
cur.close()
conn.close()

print("✅ Dummy data inserted successfully!")
