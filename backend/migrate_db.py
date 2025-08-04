import sqlite3
import os

def migrate_database():
    """Add missing columns to make RSS ingestion work with existing database."""
    db_path = 'data/articles.db'
    
    if not os.path.exists(db_path):
        print("Database doesn't exist, will be created on first ingestion")
        return
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        # Add missing columns if they don't exist
        missing_columns = [
            ("published_date", "TEXT"),
            ("description", "TEXT"),
            ("source_url", "TEXT"),
            ("tags", "TEXT"),
            ("content_length", "INTEGER"),
            ("content_parsed_at", "TEXT"),
            ("content_parser_method", "TEXT"),
            ("content_metadata", "TEXT")
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                    print(f"Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    print(f"Error adding {col_name}: {e}")
        
        # Copy data from published_at to published_date if needed
        if "published_date" not in columns:
            cursor.execute("UPDATE articles SET published_date = published_at WHERE published_at IS NOT NULL")
            print("Copied published_at to published_date")
        
        # Update content_length based on existing content
        cursor.execute("UPDATE articles SET content_length = LENGTH(content) WHERE content IS NOT NULL")
        print("Updated content_length column")
        
        # Create indexes if they don't exist
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_source ON articles(source)",
            "CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date)",
            "CREATE INDEX IF NOT EXISTS idx_content_length ON articles(content_length)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError as e:
                print(f"Index creation error: {e}")
        
        print("Database migration completed!")

if __name__ == "__main__":
    migrate_database()
