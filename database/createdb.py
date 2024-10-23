import sqlite3

# Database file name
DB_NAME = "booking_system.db"

# SQL Queries to Create Tables
TABLES = {
    'ServiceAvailability': '''
    CREATE TABLE IF NOT EXISTS ServiceAvailability (
        id INTEGER PRIMARY KEY,
        studio_location TEXT,
        service_name TEXT,
        employee_id INTEGER,
        employee_name TEXT,
        appointment_date DATE,
        appointment_time TIME,
        is_available BOOLEAN
    );
    ''',
    'Appointment': '''
    CREATE TABLE IF NOT EXISTS Appointment (
    appointment_id INTEGER PRIMARY KEY,
    service_availability_id INTEGER,
    customer_name TEXT NOT NULL,
    customer_contact TEXT,
    service_name TEXT,
    service_price INTEGER,
    employee_id INTEGER,
    employee_name TEXT,
    studio_location TEXT,
    appointment_date DATE,
    appointment_time TIME,
    status TEXT CHECK(status IN ('Scheduled', 'Completed', 'Cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_availability_id) REFERENCES ServiceAvailability(id)
);
''',
'StudioLocation':''' 
CREATE TABLE IF NOT EXISTS StudioLocation (
    studio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    studio_name TEXT NOT NULL,
    city TEXT NOT NULL,
    address TEXT,
    UNIQUE(studio_name, city)  -- Ensures no duplicate studios in the same city
);
''',
'Services': '''CREATE TABLE IF NOT EXISTS Services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price_mittel_without_card REAL,
    price_munich_without_card REAL,
    price_mittel_with_card REAL,
    price_munich_with_card REAL
);
'''
}

def connect_and_create_tables():
    """Connects to the SQLite database and creates all tables."""
    try:
        # Connect to SQLite database (creates the file if it doesn't exist)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Create each table defined in the TABLES dictionary
        for table_name, create_table_query in TABLES.items():
            cursor.execute(create_table_query)
            print(f"Table '{table_name}' created successfully.")

        # Commit changes and close the connection
        conn.commit()
        cursor.close()
        conn.close()
        print("All tables created successfully.")

    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

def insert_sample_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # sample_data = [
    #     (1, 'Cologne', 'Bikini classic', 101, 'Anna', '2023-10-05', '14:00:00', True),
    #     (2, 'Cologne', 'Bikini classic', 102, 'Maria', '2023-10-05', '15:00:00', True),
    #     (3, 'Cologne', 'Bikini classic', 103, 'Sofia', '2023-10-05', '16:30:00', True),
    #     (4, 'Cologne', 'Bikini classic', 101, 'Anna', '2023-10-05', '14:00:00', False)
    # ]
    
#     data = [
#         ('Senzera Studio', 'Berlin', 'Alexanderplatz 1, 10178 Berlin'),
# ('Senzera Studio', 'Hamburg', 'Mönckebergstraße 7, 20095 Hamburg'),
# ('Senzera Studio', 'Cologne', 'Hohe Straße 100, 50667 Cologne')
#     ]
#     cursor.executemany('''
#                        INSERT INTO StudioLocation (studio_name, city, address) VALUES (?, ?, ?)
#                        ''',data )
    
    # cursor.executemany('''
    #     INSERT INTO ServiceAvailability (
    #         id, studio_location, service_name, employee_id, employee_name, appointment_date, appointment_time, is_available
    #     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    # ''', sample_data)
    
    # services_list = [
    #     ('Oberschenkel', 'Sugaring', 39.0, 40.0, 31.0, 31.0),
    #     ('Unterschenkel', 'Sugaring', 39.0, 40.0, 31.0, 31.0),
    #     ('Beine complete', 'Sugaring', 65.0, 67.0, 53.0, 54.0),
    #     ('Bikini classic', 'Sugaring', 28.0, 29.0, 21.0, 22.0),
    #     ('Bikini brazilian', 'Sugaring', 37.0, 37.0, 28.0, 29.0),
    #     ('Men zone intim', 'Sugaring', 65.0, 65.0, 53.0, 53.0),
    #     ('Po', 'Sugaring', 26.0, 26.0, 21.0, 21.0),
    #     ('Rücken unten', 'Sugaring', 31.0, 32.0, 25.0, 26.0),
    #     ('Schultern', 'Sugaring', 42.0, 43.0, 35.0, 36.0)
    # ]
    
    # cursor.executemany(
    # ''' INSERT INTO Services (
    # service_name, category, 
    # price_mittel_without_card, price_munich_without_card, 
    # price_mittel_with_card, price_munich_with_card
    # ) VALUES (?,?,?,?,?,?) ''', services_list)

    
    conn.commit()
    cursor.close()
    conn.close()
    print("Sample data inserted successfully.")




if __name__ == "__main__":
    # Create the database and tables
    connect_and_create_tables()
    # insert_sample_data()