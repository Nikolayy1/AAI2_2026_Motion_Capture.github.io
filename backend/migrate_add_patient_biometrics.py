import sqlite3

def migrate():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(patients)")
    columns = [column[1] for column in cursor.fetchall()]

    # Add biometric columns to patients table if they don't exist
    if 'age' not in columns:
        cursor.execute('ALTER TABLE patients ADD COLUMN age INTEGER')
        print("Added 'age' column to patients table")

    if 'gender' not in columns:
        cursor.execute('ALTER TABLE patients ADD COLUMN gender TEXT')
        print("Added 'gender' column to patients table")

    if 'height' not in columns:
        cursor.execute('ALTER TABLE patients ADD COLUMN height REAL')
        print("Added 'height' column to patients table")

    if 'weight' not in columns:
        cursor.execute('ALTER TABLE patients ADD COLUMN weight REAL')
        print("Added 'weight' column to patients table")

    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
