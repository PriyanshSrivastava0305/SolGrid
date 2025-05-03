import mysql.connector

def initialize_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="system",
        database="solar_db"
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            capacity VARCHAR(255),
            location VARCHAR(255),
            latitude FLOAT,
            longitude FLOAT
        )
    """)
    conn.commit()
    return conn

def save_data(conn, data):
    cursor = conn.cursor()
    for project in data:
        cursor.execute("""
            INSERT INTO projects (name, capacity, location, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            project["name"],
            project["capacity"],
            project["location"],
            project["latitude"],
            project["longitude"]
        ))
    conn.commit()