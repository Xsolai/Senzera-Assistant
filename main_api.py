import datetime
from fastapi import FastAPI 
import sqlite3

app = FastAPI()

# Database connection helper
def create_connection():
    """Create a connection to the SQLite database."""
    try:
        conn = sqlite3.connect("booking_system.db")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

@app.get("/total_booked_services")
def get_total_booked_services():
    """
    Retrieve the total number of booked services from the Appointment table.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Query to get the total number of booked services
        cursor.execute("SELECT COUNT(*) FROM Appointment;")
        result = cursor.fetchone()
        total_booked = result[0] if result else 0

        return {"total_booked_services": total_booked}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()

@app.get("/total_appointments")
def total_appointments_api():
    """
    Retrieve the total number of appointments from the Appointment table.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Query to get the total number of appointments
        cursor.execute("SELECT COUNT(*) FROM Appointment;")
        result = cursor.fetchone()
        total_appointments = result[0] if result else 0

        return {"total_appointments": total_appointments}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

@app.get("/total_revenue")
def total_revenue_api():
    """
    API endpoint to retrieve the total revenue generated from appointments.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Query to calculate the total revenue
        cursor.execute("SELECT SUM(service_price) FROM Appointment;")
        result = cursor.fetchone()
        total_revenue = result[0] if result[0] is not None else 0.0

        return {"total_revenue": total_revenue}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()

@app.get("/appointment_details")
def get_appointment_details():
    """
    API endpoint to retrieve details of all appointments.
    Includes service name, date, time, location, status, and revenue.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Query to get the appointment details
        cursor.execute("""
            SELECT 
                service_name, 
                appointment_date, 
                appointment_time, 
                studio_location, 
                status, 
                service_price 
            FROM Appointment;
        """)
        appointments = cursor.fetchall()

        # Format the result into a list of dictionaries
        formatted_appointments = [
            {
                "service_name": row[0],
                "appointment_date": row[1],
                "appointment_time": row[2],
                "studio_location": row[3],
                "status": row[4],
                "revenue": row[5]
            }
            for row in appointments
        ]

        return {"appointments": formatted_appointments}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()

@app.get("/service_popularity")
def get_service_popularity():
    """
    API endpoint to fetch the popularity of services based on the number of bookings.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Query to calculate the number of bookings for each service
        cursor.execute("""
            SELECT 
                service_name, 
                COUNT(*) AS total_bookings 
            FROM Appointment
            GROUP BY service_name
            ORDER BY total_bookings DESC;
        """)

        services = cursor.fetchall()

        # Format the result as a list of dictionaries
        formatted_services = [
            {"service_name": row[0], "total_bookings": row[1]} for row in services
        ]

        return {"service_popularity": formatted_services}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()

@app.get("/area_distribution")
def get_area_distribution():
    """
    API endpoint to fetch the distribution of bookings across different cities or areas.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Query to calculate the number of bookings for each location
        cursor.execute("""
            SELECT 
                studio_location AS city, 
                COUNT(*) AS total_bookings 
            FROM Appointment
            GROUP BY studio_location
            ORDER BY total_bookings DESC;
        """)

        areas = cursor.fetchall()

        # Format the result as a list of dictionaries
        formatted_areas = [
            {"city": row[0], "total_bookings": row[1]} for row in areas
        ]

        return {"area_distribution": formatted_areas}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()

@app.post("/update_appointment_status")
def update_appointment_status():
    """
    API to update appointment statuses:
    - 'Scheduled' for future appointments
    - 'Completed' for past appointments
    - Skips 'Cancelled' appointments
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Get the current date and time
        current_time = datetime.now()

        # Step 1: Update status to 'Completed' for past appointments
        cursor.execute("""
            UPDATE Appointment
            SET status = 'Completed'
            WHERE status = 'Scheduled'
              AND datetime(appointment_date || ' ' || appointment_time) < ?;
        """, (current_time.strftime('%Y-%m-%d %H:%M:%S'),))

        # Step 2: Update status to 'Scheduled' for upcoming appointments
        cursor.execute("""
            UPDATE Appointment
            SET status = 'Scheduled'
            WHERE status != 'Cancelled'
              AND datetime(appointment_date || ' ' || appointment_time) >= ?;
        """, (current_time.strftime('%Y-%m-%d %H:%M:%S'),))

        conn.commit()
        return {"success": "Appointment statuses updated successfully."}

    except sqlite3.Error as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()

# Run the app using: uvicorn filename:app --reload
