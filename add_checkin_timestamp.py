from sqlalchemy import create_engine, MetaData, Table, Column, DateTime
from database import engine
import sqlite3

def run_migration():
    print("Starting migration: Adding checked_in_at column to QRCode table...")
    
    try:
        # Using SQLite-specific ALTER TABLE command
        conn = sqlite3.connect('qrcodes.db')
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(qrcodes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'checked_in_at' not in columns:
            cursor.execute("ALTER TABLE qrcodes ADD COLUMN checked_in_at TIMESTAMP")
            print("Successfully added checked_in_at column to qrcodes table")
        else:
            print("Column checked_in_at already exists in qrcodes table")
        
        conn.commit()
        conn.close()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    run_migration() 