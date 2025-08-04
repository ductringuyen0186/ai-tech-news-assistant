import sqlite3

# Connect to the database
conn = sqlite3.connect('data/articles.db')

# Get all tables
print("Tables:")
for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(f"  - {row[0]}")

# Check if articles table exists and get its schema
try:
    print("\nArticles table schema:")
    for row in conn.execute("PRAGMA table_info(articles)"):
        print(f"  {row[1]} ({row[2]}) - {row}")
except sqlite3.OperationalError as e:  
    print(f"Error: {e}")

conn.close()
