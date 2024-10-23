# Dashboard APIs
This project provides a set of APIs to manage appointments, services, and analytics for a studio booking system.

Prerequisites
Make sure you have the following installed:

Python 3.x
FastAPI
Uvicorn (to run the server)
SQLite3 (for database)
Install required Python packages:

bash
Copy code
pip install fastapi uvicorn sqlite3
How to Run the API Server
Navigate to the Project Directory
Open your terminal and go to the directory where your project files are located.

Run the API Server
Use the following command to start the API server using Uvicorn:

bash
Copy code
uvicorn main_api:app --reload
main_api.py is the entry point to the FastAPI app.
Access the APIs
Once the server is running, you can access the APIs at:

http://127.0.0.1:8000
Available APIs
Confirm Appointment API

Endpoint: /confirm_appointment
Method: POST
Description: Confirms a new appointment and stores the service price.
Payload:
json
Copy code
{
  "customer_name": "Jason Roy",
  "customer_contact": "0333-3090909",
  "city": "Cologne",
  "service_name": "Bikini classic",
  "appointment_date": "2023-10-05",
  "appointment_time": "14:00:00",
  "price_category": "munich_with_card"
}
Update Appointment Status API

Endpoint: /update_appointment_status
Method: POST
Description: Updates appointment statuses based on the current time.
Get All Appointments API

Endpoint: /appointments
Method: GET
Description: Retrieves details of all appointments.
Service Popularity API

Endpoint: /service_popularity
Method: GET
Description: Fetches the popularity of services based on the number of bookings.
Area Distribution API

Endpoint: /area_distribution
Method: GET
Description: Fetches the distribution of bookings across different cities.
Testing the APIs
Using Postman or Browser:

You can use Postman or any API testing tool to test the endpoints.
For GET requests, you can also use your web browser to view the response.
Example for Testing with cURL:

bash
Copy code
curl -X POST http://127.0.0.1:8000/confirm_appointment \
-H "Content-Type: application/json" \
-d '{
  "customer_name": "Jason Roy",
  "customer_contact": "0333-3090909",
  "city": "Cologne",
  "service_name": "Bikini classic",
  "appointment_date": "2023-10-05",
  "appointment_time": "14:00:00",
  "price_category": "price_mittel_without_card"
}'