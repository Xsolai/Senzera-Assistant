import sqlite3

def create_connection():
    try:
        conn = sqlite3.connect('booking_system.db')
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def delete_tables(table_names):
    try:
        conn = create_connection()
        if not conn:
            print("Failed to connect to the database.")
            return

        cursor = conn.cursor()

        # Delete tables with specified names
        for table_name in table_names:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            print(f"Table '{table_name}' deleted successfully (if it existed).")

        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Provide the table names you want to deleteclear
    tables_to_delete = ['Services']
    delete_tables(tables_to_delete)
