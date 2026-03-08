import sqlite3

conn = sqlite3.connect("jobs.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT DEFAULT 'Manual',
    file_name TEXT,
    file_path TEXT,
    assigned_user TEXT DEFAULT 'Unassigned',
    status TEXT DEFAULT 'Received',
    position REAL
)            
""")

conn.commit()
conn.close()

print("Database Initialised")