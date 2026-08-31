import sqlite3

conn = sqlite3.connect("database.db")  # change name if yours is different
cur = conn.cursor()

# show all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("TABLES:", cur.fetchall())

# view one table (change "users" if needed)
table_name = "users"

try:
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()

    print(f"\nDATA FROM {table_name}:")
    for row in rows:
        print(row)

except Exception as e:
    print("Error:", e)

conn.close()