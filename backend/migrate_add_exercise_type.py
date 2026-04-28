#!/usr/bin/env python3
"""
Migration script to add exercise_type column to existing database
Run this once to update your database schema
"""

import sqlite3

DATABASE_PATH = "./app.db"

def migrate():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'exercise_type' in columns:
            print("✓ exercise_type column already exists!")
        else:
            # Add the exercise_type column
            cursor.execute("""
                ALTER TABLE submissions
                ADD COLUMN exercise_type TEXT
            """)
            conn.commit()
            print("✓ Successfully added exercise_type column to submissions table!")

    except sqlite3.Error as e:
        print(f"✗ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running migration to add exercise_type column...")
    migrate()
    print("Migration complete!")
