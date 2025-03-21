#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Подключение к базе данных
conn = sqlite3.connect('smart_home.db')
cursor = conn.cursor()

# Пример записи данных
sensor_name = "temperature_sensor"
value = 23.5
timestamp = datetime.now()

cursor.execute("""
    INSERT INTO sensor_data (sensor_name, value, timestamp)
    VALUES (?, ?, ?)
""", (sensor_name, value, timestamp))

conn.commit()
conn.close()

print("Данные успешно записаны!")
