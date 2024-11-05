import os
import sqlite3

# Set the path for the database in the instance folder
DATABASE_PATH = 'instance/database.db'


def init_db():
    # Initialize the database with a simple table for profiles if it doesn't exist
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT UNIQUE NOT NULL
            )
        """)
        conn.commit()

# Initialize the database
init_db()
