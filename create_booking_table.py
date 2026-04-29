import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    trip_name TEXT,
    full_name TEXT,
    phone TEXT,
    people INTEGER,
    trip_date TEXT,
    note TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Tabel bookings berhasil dibuat")