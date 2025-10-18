import sqlite3
import os

# Check both database files
dbs = [
    'data/articles.db',
    'data/ai_news.db',
    './data/articles.db',
    './data/ai_news.db'
]

for db_path in dbs:
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            print(f"{db_path}: {count} articles")
            conn.close()
        except Exception as e:
            print(f"{db_path}: Error - {e}")
