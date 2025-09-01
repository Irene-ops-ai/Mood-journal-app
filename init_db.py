import sqlite3

# Connect (creates journal.db if not exists)
conn = sqlite3.connect("journal.db")
cursor = conn.cursor()

# Load SQL from file
with open("journal.sql", "r") as f:
    sql_script = f.read()

cursor.executescript(sql_script)
conn.commit()
conn.close()

print("✅ Database journal.db created successfully!")
