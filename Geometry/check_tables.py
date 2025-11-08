import sqlite3

conn = sqlite3.connect('geometry_learning.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in geometry_learning.db:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()
