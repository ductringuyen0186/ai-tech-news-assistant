import sqlite3

conn = sqlite3.connect('data/articles.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM articles')
total = cursor.fetchone()[0]
print(f'Total articles: {total}')

cursor.execute('SELECT title, source, published_date FROM articles ORDER BY created_at DESC LIMIT 5')
print('Recent articles:')
for row in cursor.fetchall():
    title = row[0][:60] + "..." if len(row[0]) > 60 else row[0]
    print(f'  - {title} ({row[1]}) - {row[2]}')

conn.close()
