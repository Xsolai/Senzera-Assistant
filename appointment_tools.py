from datetime import datetime
import sqlite3
# from utilities import determine_price_category
# from assitant import last_response
DB_NAME = "booking_system.db"


def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    return conn

""" Check Studio Exist in the city"""
def check_studio_exists(city: str, studio_name: str):
    """
    Check if a specific studio exists in the given city.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Failed to connect to the database."}

        cursor = conn.cursor()

        # Query to check if the studio exists
        query = """
        SELECT 1 FROM StudioLocation 
        WHERE city = ? AND studio_name = ?;
        """
        cursor.execute(query, (city, studio_name))
        result = cursor.fetchone()

        if result:
            return {"success": f"Studio '{studio_name}' exists in {city}."}
        else:
            return {"error": f"Studio '{studio_name}' does not exist in {city}."}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()
def get_sites(city_name: str) -> str:
    """Retrieve all studios in a specific city."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT studio_location FROM ServiceAvailability WHERE LOWER(studio_location) = LOWER(?);
        """
        cursor.execute(query, (city_name,))
        sites = cursor.fetchall()

        if not sites:
            return f"We do not have any studios in {city_name}."
        
        return f"Studios in {city_name}: {', '.join(site[0] for site in sites)}"

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return "Error retrieving studios."
    finally:
        if conn:
            conn.close()

def get_product(studio_location: str, service_name: str) -> str:
    """Check if a specific service is offered at a specific studio location."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT service_name FROM ServiceAvailability WHERE LOWER(studio_location) = LOWER(?) AND LOWER(service_name) = LOWER(?);
        """
        cursor.execute(query, (studio_location, service_name))
        service = cursor.fetchone()

        if not service:
            return f"Sorry, '{service_name}' is not offered at our {studio_location} studio."
        
        return f"Yes, we offer '{service_name}' at our {studio_location} studio."

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return "Error checking service availability."
    finally:
        if conn:
            conn.close()

def get_employees(studio_location: str, service_name: str, appointment_date: str, appointment_time: str):
    """Retrieve employees who are available to perform a specific service at a studio on a specific date and time."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT employee_id, employee_name FROM ServiceAvailability
        WHERE LOWER(studio_location) = LOWER(?) AND LOWER(service_name) = lOWER(?) AND appointment_date = ? AND appointment_time = ? AND is_available = 1;
        """
        cursor.execute(query, (studio_location, service_name, appointment_date, appointment_time))
        employees = cursor.fetchall()

        if not employees:
            return f"No available employees found for '{service_name}' at our {studio_location} studio on {appointment_date} at {appointment_time}."
        
        return employees

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        if conn:
            conn.close()

# def get_suggestions(studio_location: str, service_name: str, appointment_date: str):
#     """Retrieve a list of available appointment dates and times for a specific service at a studio."""
#     try:
#         conn = create_connection()  # Assuming create_connection() is defined elsewhere to connect to your DB
#         cursor = conn.cursor()

#         # Query to get available appointment dates and times for the specified service and studio
#         query = """
#         SELECT DISTINCT appointment_date, appointment_time
#         FROM ServiceAvailability
#         WHERE studio_location = ? 
#           AND service_name = ? 
#           AND appointment_date = ?
#           AND is_available = 1
#         ORDER BY appointment_date, appointment_time;
#         """
#         cursor.execute(query, (studio_location, service_name, appointment_date))
#         available_slots = cursor.fetchall()

#         if not available_slots:
#             return f"No available appointment slots for '{service_name}' at our {studio_location} studio currently."

#         # Format the output to be user-friendly
#         suggestions = [
#             {"appointment_date": slot[0], "appointment_time": slot[1]}
#             for slot in available_slots
#         ]
#         print("Suggestions: ", suggestions)
#         return suggestions

#     except sqlite3.Error as e:
#         print(f"An error occurred: {e}")
#         return []
#     finally:
#         if conn:
#             conn.close()

def get_suggestions(studio_location: str, service_name: str, appointment_date: str, appointment_time: str = None):
    """Retrieve a list of available appointment dates and times for a specific service at a studio."""
    try:
        conn = create_connection()  # Assuming create_connection() is defined elsewhere to connect to your DB
        cursor = conn.cursor()

        # Base query for available appointments
        query = """
        SELECT DISTINCT appointment_date, appointment_time
        FROM ServiceAvailability
        WHERE LOWER(studio_location) = LOWER(?) 
          AND LOWER(service_name) = LOWER(?)
          AND appointment_date = ? 
          AND is_available = 1
        """

        params = [studio_location, service_name, appointment_date]

        # Add filtering by time if appointment_time is provided
        if appointment_time:
            query += " AND appointment_time = ?"
            params.append(appointment_time)

        query += " ORDER BY appointment_date, appointment_time;"

        # Execute the query with the appropriate parameters
        cursor.execute(query, tuple(params))
        available_slots = cursor.fetchall()

        if not available_slots:
            if appointment_time:
                return (f"No available slot for '{service_name}' at {studio_location} "
                        f"on {appointment_date} at {appointment_time}.")
            return (f"No available slots for '{service_name}' at {studio_location} "
                    f"on {appointment_date}.")

        # Format the output to be user-friendly
        suggestions = [
            {"appointment_date": slot[0], "appointment_time": slot[1]}
            for slot in available_slots
        ]
        print("Suggestions: ", suggestions)
        return suggestions

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        if conn:
            conn.close()

"""" For Booking An Appointment """
# def confirm_appointment(
#     customer_name, customer_contact, city, 
#     service_name, appointment_date, appointment_time
# ):
#     try:
#         conn = create_connection()
#         cursor = conn.cursor()
#         # Step 1: Fetch the service availability ID
#         cursor.execute("""
#             SELECT id FROM ServiceAvailability
#             WHERE studio_location = ? 
#             AND service_name = ? 
#             AND appointment_date = ? 
#             AND appointment_time = ? 
#             AND is_available = TRUE;
#         """, (city, service_name, appointment_date, appointment_time))
        
#         result = cursor.fetchone()
#         if not result:
#             return {"error": "No available service found for the given time and location."}
        
#         service_availability_id = result[0]

#         # Step 2: Insert confirmed appointment into Appointment table
#         cursor.execute("""
#             INSERT INTO Appointment (
#                 service_availability_id, customer_name, customer_contact, 
#                 service_name, employee_id, employee_name, studio_location, 
#                 appointment_date, appointment_time, status
#             ) 
#             SELECT 
#                 sa.id, ?, ?, sa.service_name, sa.employee_id, sa.employee_name, 
#                 sa.studio_location, sa.appointment_date, sa.appointment_time, 'Scheduled'
#             FROM ServiceAvailability sa
#             WHERE sa.id = ?;
#         """, (customer_name, customer_contact, service_availability_id))
        
#         # Retrieve the appointment_id of the newly inserted appointment
#         appointment_id = cursor.lastrowid
        
#         # Step 3: Update the availability status to 0 (unavailable)
#         cursor.execute("""
#             UPDATE ServiceAvailability
#             SET is_available = 0
#             WHERE id = ?;
#         """, (service_availability_id,))
        
#         conn.commit()
#         return {"success": f"{customer_name} your Appointment confirmed successfully with appointment id: {appointment_id}."}
#     except sqlite3.Error as e:
#         conn.rollback()
#         print(f"An error occurred: {e}")
#         return []
#     finally:
#         if conn:
#             conn.close()


# def confirm_appointment(
#     customer_name, customer_contact, city, 
#     service_name, appointment_date, appointment_time
# ):
#     """
#     Confirm an appointment, fetch service price based on price category,
#     and store it in the appointment.
#     """
#     try:
#         conn = create_connection()
#         if not conn:
#             return {"error": "Database connection failed."}

#         cursor = conn.cursor()

#         # Step 1: Fetch the service availability ID
#         cursor.execute("""
#             SELECT id 
#             FROM ServiceAvailability
#             WHERE studio_location = ? 
#               AND service_name = ? 
#               AND appointment_date = ? 
#               AND appointment_time = ? 
#               AND is_available = TRUE;
#         """, (city, service_name, appointment_date, appointment_time))

#         result = cursor.fetchone()
#         if not result:
#             return {"error": "No available service found for the given time and location."}

#         service_availability_id = result[0]

#         # Step 2: Fetch the service price from the Services table
#         try:
#             # print("Last Response: ", last_response)
#             # price_category = determine_price_category(city,last_response )
#             price_category = ''
#             print("Price Input from Chatbot:", price_category)
#         except e:
#             print(f"Price Category Error: {e}")
        
        
#         # if price_category is None:
#         #     # price_category = 'price_mittel_with_card'
            
#         if not price_category:
#             return {"error": f"Invalid price category: {price_category}"}

#         cursor.execute(f"""
#             SELECT {price_category} 
#             FROM Services 
#             WHERE service_name = ?;
#         """, (service_name,))
        
#         price_result = cursor.fetchone()
#         print("Price from Serive Table:",price_result)
#         if not price_result:
#             return {"error": f"No price found for service {service_name}."}

#         service_price = price_result[0]
#         print("final price:", service_price)
#         # Step 3: Insert confirmed appointment into Appointment table
#         cursor.execute("""
#             INSERT INTO Appointment (
#                 service_availability_id, customer_name, customer_contact, 
#                 service_name, employee_id, employee_name, studio_location, 
#                 appointment_date, appointment_time, status, service_price
#             ) 
#             SELECT 
#                 sa.id, ?, ?, sa.service_name, sa.employee_id, sa.employee_name, 
#                 sa.studio_location, sa.appointment_date, sa.appointment_time, 
#                 'Scheduled', ?
#             FROM ServiceAvailability sa
#             WHERE sa.id = ?;
#         """, (customer_name, customer_contact, service_price, service_availability_id))

#         # Retrieve the appointment_id of the newly inserted appointment
#         appointment_id = cursor.lastrowid

#         # Step 4: Update the availability status to 0 (unavailable)
#         cursor.execute("""
#             UPDATE ServiceAvailability
#             SET is_available = 0
#             WHERE id = ?;
#         """, (service_availability_id,))

#         conn.commit()

#         return {
#             "success": f"{customer_name}, your appointment was confirmed successfully with appointment ID: {appointment_id}.",
#             "service_price": service_price
#         }

#     except sqlite3.Error as e:
#         conn.rollback()
#         print(f"An error occurred: {e}")
#         return {"error": str(e)}

#     finally:
#         if conn:
#             conn.close()

def confirm_appointment(
    customer_name, customer_contact, city, 
    service_name, appointment_date, appointment_time, s_card, user_id
):
    """
    Confirm an appointment, fetch service price based on price category 
    (dependent on city and s_card), and store it in the appointment.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Step 1: Fetch the service availability ID
        cursor.execute("""
            SELECT id 
            FROM ServiceAvailability
            WHERE LOWER(studio_location) = LOWER(?) 
              AND LOWER(service_name) = LOWER(?)
              AND appointment_date = ? 
              AND appointment_time = ? 
              AND is_available = TRUE;
        """, (city, service_name, appointment_date, appointment_time))

        result = cursor.fetchone()
        if not result:
            return {"error": "No available service found for the given time and location."}

        service_availability_id = result[0]

        # Step 2: Determine the price category based on city and s_card value
        price_category = None

        if city.lower() == "munich":
            if s_card.lower() == "yes":
                price_category = "price_munich_with_card"
            else:
                price_category = "price_munich_without_card"
        else:
            if s_card.lower() == "yes":
                price_category = "price_mittel_with_card"
            else:
                price_category = "price_mittel_without_card"

        print("Price Category: ", price_category)
        # Validate if the price category is determined
        if not price_category:
            return {"error": f"Invalid price category for city: {city} and s_card: {s_card}"}

        # Step 3: Fetch the service price from the Services table
        cursor.execute(f"""
            SELECT {price_category} 
            FROM Services 
            WHERE LOWER(service_name) = LOWER(?);
        """, (service_name,))
        
        price_result = cursor.fetchone()
        print("Price: ", price_result)
        if not price_result:
            return {"error": f"No price found for service {service_name} with category {price_category}."}

        service_price = price_result[0]
        # print("Service Price: ", service_price)
        # Step 4: Insert confirmed appointment into the Appointment table
        cursor.execute("""
        INSERT INTO Appointment (
            service_availability_id, user_id, customer_name, customer_contact, 
            service_name, employee_id, employee_name, studio_location, 
            appointment_date, appointment_time, status, service_price
        ) 
        SELECT 
            sa.id, ?, ?, ?, sa.service_name, sa.employee_id, sa.employee_name, 
            sa.studio_location, sa.appointment_date, sa.appointment_time, 
            'Scheduled', ?
        FROM ServiceAvailability sa
        WHERE sa.id = ?;
    """, (user_id, customer_name, customer_contact, service_price, service_availability_id))

        #(customer_name, customer_contact, service_price, service_availability_id))

        # Retrieve the appointment_id of the newly inserted appointment
        appointment_id = cursor.lastrowid

        # Step 5: Update the availability status to 0 (unavailable)
        cursor.execute("""
            UPDATE ServiceAvailability
            SET is_available = 0
            WHERE id = ?;
        """, (service_availability_id,))

        conn.commit()

        return {
            "success": f"{customer_name}, your appointment was confirmed successfully with appointment ID: {appointment_id}.",
            "service_price": service_price
        }

    except sqlite3.Error as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()


""" Cancel An Appointment """
def cancel_appointment(appointment_id: int, user_id: int):
    """
    Cancel a confirmed appointment by removing it from the database using the appointment ID
    and user ID for validation. Also sets the corresponding service availability back to 
    available (is_available = 1) if the appointment exists and matches the provided user_id.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Step 1: Check if the appointment exists and matches the user_id, fetch service_availability_id
        cursor.execute("""
            SELECT service_availability_id 
            FROM Appointment 
            WHERE appointment_id = ? AND user_id = ?;
        """, (appointment_id, user_id))
        result = cursor.fetchone()

        # If no result, either appointment doesn't exist or user_id doesn't match
        if not result:
            return {"error": f"No appointment found with ID {appointment_id} for the specified user."}

        service_availability_id = result[0]

        # Step 2: Delete the appointment
        cursor.execute("DELETE FROM Appointment WHERE appointment_id = ?", (appointment_id,))

        # Step 3: Update the service availability to 1 (available)
        cursor.execute("""
            UPDATE ServiceAvailability 
            SET is_available = 1 
            WHERE id = ?;
        """, (service_availability_id,))

        conn.commit()

        return {"success": f"Appointment with ID {appointment_id} has been cancelled successfully."}

    except sqlite3.Error as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()

def fetch_my_appointments(user_id: int):
    """
    Fetch current and future appointments for a user based on user_id.
    Returns appointments scheduled from today's date onwards.
    """
    try:
        conn = create_connection()
        if not conn:
            return {"error": "Database connection failed."}

        cursor = conn.cursor()

        # Step 1: Get the current date for filtering appointments
        current_date = datetime.now().date()

        # Step 2: Query to fetch appointments for the given user_id from current to future dates
        cursor.execute("""
            SELECT appointment_id, service_name, studio_location, appointment_date, 
                   appointment_time, status, service_price
            FROM Appointment
            WHERE user_id = ? AND appointment_date >= ?
            ORDER BY appointment_date, appointment_time;
        """, (user_id, current_date))

        # Step 3: Fetch all matching results
        appointments = cursor.fetchall()

        # If no future appointments are found
        if not appointments:
            return {"message": "No current or future appointments found."}

        # Format the results for readability
        formatted_appointments = [
            {
                "appointment_id": appt[0],
                "service_name": appt[1],
                "studio_location": appt[2],
                "appointment_date": appt[3],
                "appointment_time": appt[4],
                "status": appt[5],
                "service_price": appt[6]
            }
            for appt in appointments
        ]

        return {"appointments": formatted_appointments}

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

    finally:
        if conn:
            conn.close()