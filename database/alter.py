import sqlite3

def create_connection():
    try:
        conn = sqlite3.connect('booking_system.db')
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def recreate_appointment_table_with_correct_constraint():
    try:
        conn = create_connection()
        if not conn:
            print("Failed to connect to the database.")
            return

        cursor = conn.cursor()

        # Step 1: Rename the old Appointment table
        cursor.execute("ALTER TABLE Appointment RENAME TO Appointment_old1;")

        # Step 2: Create a new Appointment table with the correct constraint
        cursor.execute("""
            CREATE TABLE Appointment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_availability_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_contact TEXT NOT NULL,
                service_name TEXT NOT NULL,
                employee_id INTEGER,
                employee_name TEXT,
                studio_location TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                status TEXT CHECK (status IN ('Confirmed', 'Completed', 'Cancelled')),
                service_price REAL,
                FOREIGN KEY (service_availability_id) REFERENCES ServiceAvailability(id)
            );
        """)

        # Step 3: Copy data from the old table to the new one
        cursor.execute("""
            INSERT INTO Appointment (
                appointment_id, service_availability_id, customer_name, customer_contact,
                service_name, employee_id, employee_name, studio_location,
                appointment_date, appointment_time, status, service_price
            )
            SELECT
                appointment_id, service_availability_id, customer_name, customer_contact,
                service_name, employee_id, employee_name, studio_location,
                appointment_date, appointment_time, status, service_price
            FROM Appointment_old;
        """)

        # Step 4: Drop the old table
        cursor.execute("DROP TABLE Appointment_old;")

        conn.commit()
        print("Appointment table updated successfully with the correct constraint.")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    recreate_appointment_table_with_correct_constraint()
