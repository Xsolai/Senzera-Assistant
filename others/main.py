import json
import os
from openai import OpenAI
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Define the tools
from tools import tools

# Implement the functions
from v1.appointment_tools import cancel_appointment, confirm_appointment, get_employees, get_sites, get_product, get_suggestions #, get_employees, get_products, get_product, book_appointment
import logging; 

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
class OpenAIAssistant:
    def __init__(self, api_key, assistant_id, model="gpt-4-1106-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.assistant_id = assistant_id
        self.thread = None
        self.run = None

    def create_thread(self):
        self.thread = self.client.beta.threads.create()
        return self.thread

    def add_message(self, content):
        if self.thread is None:
            self.create_thread()
        
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=content
        )
        return message

    def run_assistant(self, instructions=None):
        if self.thread is None:
            raise ValueError("Thread must be created before running the assistant")
        
        run_params = {
            "assistant_id": self.assistant_id,
            "thread_id": self.thread.id,
        }
        if instructions:
            run_params["instructions"] = instructions
        
        self.run = self.client.beta.threads.runs.create(**run_params)
        return self.run

    def wait_for_completion(self):
        if self.run is None:
            raise ValueError("Run must be created before waiting for completion")
        
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=self.run.id
            )
            if run_status.status == 'completed':
                return self.get_latest_message()
            elif run_status.status == 'failed':
                raise Exception(f"Run failed: {run_status.last_error}")
            elif run_status.status == 'requires_action':
                self.handle_required_action(run_status)
            time.sleep(1)

    def get_latest_message(self):
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        return messages.data[0].content[0].text.value

    def handle_required_action(self, run_status):
        tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = eval(tool_call.function.arguments)

            # get_sites, get_employees, get_products, get_product, book_appointment
            
            if function_name == "get_sites":
                
                # logging.info(f"get_sites being called at {arguments.get("city")}")
                print(f"get_sites called: {arguments.get("city")}")
                result = get_sites(arguments.get("city"))
                #print(f"get_sites result: {result}")
                # logging.info(f"get_sites results: {result}")    
            elif function_name == "get_product":
                print(f"get_product called: {arguments.get("city"), arguments.get("service_name")}")
                # logging.info(f"get_product called at :{arguments}")
                result = get_product(arguments.get("city"), arguments.get("service_name"))
                # logging.info(f"get_product result:  {result}")
                
            elif function_name == "get_employees":
                
                # get_input = arguments.get("city"), arguments.get("service_name"), arguments.get("appointment_date"), arguments.get("appointment_time")
                print(f"get_employees called {arguments.get("city"), arguments.get("service_name"), arguments.get("appointment_date"), arguments.get("appointment_time")}")
                # logging.info(f"get_employees called at :{get_input}")
                result = get_employees(arguments.get("city"), arguments.get("service_name"), arguments.get("appointment_date"), arguments.get("appointment_time"))
                # logging.info(f"get_employees result:  {result}")
            elif function_name == "get_suggestions":
                print(f"get_suggestions called: {arguments.get('city'), arguments.get("service_name"), arguments.get("date")}")
                result =  get_suggestions(arguments.get('city'), arguments.get("service_name"), arguments.get("date"))
            elif function_name == "confirm_appointment":
                
                print(f"Confirm Appointment Called: {arguments.get('customer_name'),arguments.get('customer_contact'),arguments.get("city"), arguments.get("service_name"), arguments.get("appointment_date"), arguments.get("appointment_time"), arguments.get("price_category")}")
                result = confirm_appointment(arguments.get('customer_name'),arguments.get('customer_contact'),arguments.get("city"), arguments.get("service_name"), arguments.get("appointment_date"), arguments.get("appointment_time"), arguments.get("price_category"))
            elif function_name == "cancel_appointment":
                print(f"cancel_appointment called: {arguments.get("appointment_id")} ")
                # logging.info(f"get_products called at :{arguments}")
                result = cancel_appointment(arguments.get("appointment_id"))
            #     # logging.info(f"get_products result: {result}")
            # elif function_name == "book_appointment":
                
            #     # logging.info(f"book_appointment called at {arguments}")
            #     result = book_appointment(**arguments)
            #     # logging.info(f"book_appointment result: {result}")
            else:
                # logging.info(f"There is not {function_name} available.")
                result = f"Function {function_name} not implemented"

            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": str(result)
            })

        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tool_outputs
        )

    def get_current_date_and_month(self):
        # Get current date
        today = datetime.today()
        current_date = today.strftime('%Y-%m-%d')

        # Get first and last date of the current month
        first_day = today.replace(day=1)
        next_month = first_day.replace(month=today.month % 12 + 1, day=1)
        last_day = next_month - timedelta(days=1)

        # Generate a list of all dates in the current month
        dates_in_month = [(first_day + timedelta(days=i)).strftime('%Y-%m-%d') 
                        for i in range((last_day - first_day).days + 1)]

        return current_date, dates_in_month
    
    def chat(self):
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                print("Assistant: Please enter a valid message.")
                continue

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Assistant: Goodbye!")
                break

            self.add_message(user_input)
            self.run_assistant()
            response = self.wait_for_completion()
            print(f"Assistant: {response}")
            return user_input[-1]

    def process_input(self, user_input):
        """Process the given input and return the response."""
        # if not user_input.strip():
        #     return "Assistant: Please enter a valid message."

        # if user_input.lower() in ['exit', 'quit', 'bye']:
        #     return "Assistant: Goodbye!"

        # Process the message
        self.add_message(user_input)
        self.run_assistant()
        response = self.wait_for_completion()
        return response
    
# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create the assistant
assistant = client.beta.assistants.create(
    name="Senzera AI",
    instructions=f""" 
You are Senzera AI, the official virtual assistant for Senzera, a leading beauty and waxing service provider with over 60 studios across Germany and Austria. Your primary role is to assist customers in booking, modifying, or canceling their appointments seamlessly, while also providing detailed information about Senzera’s services, pricing, and studio locations. You are responsible for creating a welcoming and professional environment through WhatsApp by answering inquiries, offering personalized suggestions, and facilitating smooth appointment management.
About Senzera:
Founded in 2004, Senzera specializes in high-quality waxing, sugaring, and permanent hair removal services for both men and women. Senzera also offers a wide range of beauty treatments, including facials, nail care, and anti-aging treatments. With locations in major cities like Berlin, Munich, Cologne, Vienna, and others, Senzera is dedicated to providing smooth skin and professional care through its well-trained beauticians and personalized service options.
Senzera’s Beauty-Abo (a beauty subscription plan) allows customers to receive regular beauty treatments at discounted rates, and the company uses top-tier products like its Senzera Cosmetics line, developed in Germany for post-treatment care.
Core Responsibilities:
Natural Language Understanding (NLU):
Entity Extraction: Identify and extract key entities from user inputs, including:
Service: Examples include "Brazilian wax," "Bikini classic," "permanent hair removal," or "facial."
Date: Handle relative and absolute date formats (e.g., “tomorrow,” “July 15th,” “next Monday”).
Time: Accept and parse times in multiple formats like “2 PM,” “14:00,” or “morning/afternoon.”
Location: Understand city names or specific Senzera studio names (e.g., “Berlin studio,” “Vienna”).
price_category: 
You are a smart assistant helping users select the right price category. The user may say whether they have a card or not, but they may also answer indirectly (e.g., "Yes," "I do," or "No," "I don't"). Your job is to decide which category fits based on their response. 

Categories:
- If the user has a card and is in Munich, select "price_munich_with_card."
- If the user does not have a card and is in Munich, select "price_munich_without_card."
- If the user has a card and is in Mittel, select "price_mittel_with_card."
- If the user does not have a card and is in Mittel, select "price_mittel_without_card."

Now, based on the location and response below, return the correct price category directly.

Additional Preferences: Identify any additional preferences, such as preferred staff members, specific treatment preferences (e.g., "sensitive skin treatment").
Contextual Understanding:
Maintain context throughout multi-turn conversations, keeping track of user inputs like service type, time, and location. Dynamically prompt for missing information as needed, while ensuring a fluid, conversational experience.
Complex Requests: Manage complex requests where users ask for multiple services or multiple locations in a single session (e.g., “I want a Brazilian wax and facial in Berlin on Monday”).
Interruptions and Corrections:
Allow users to modify or correct previously provided information during the conversation. Ensure smooth transitions and maintain flexibility to update details like location, service, or time without starting over.
Handling Overlapping Appointments:


If a user attempts to book multiple services that overlap in time, resolve the conflict by suggesting new time slots or asking which service takes priority.
API Endpoints to Utilize:
get_sites: Retrieve available Senzera studios based on user input `Always use this whenver you get city name to verify that studio exist or not`.
get_products: Check which services (e.g., waxing, sugaring, permanent hair removal, facials) are offered at specific locations.
get_employees: Check staff availability for specific services or preferences.
get_suggestions: retrieve avaiable appointment slots in specfici location
confirm_appointment(): to book an appointment.
...

When a user provides a location, the bot should ask if they have the relevant S-Card for that area: if the location is Munich, ask if they have an S-Card Munich, and if it’s any other location, ask if they have an S-Card Mittle. Based on the user’s response, select the appropriate price category:
You must choose one of the category return this as argument of price_category when calling confirm_appointment() tool from these`"price_munich_with_card"` or `"price_munich_without_card"` for Munich, and `"price_mittel_with_card"` or `"price_mittel_without_card"` for other locations. The bot should only ask whether the user has the relevant card, not mention the specific price categories, which are processed internally to ensure accurate pricing is applied.

dates will be here.
                   
You have Current date and month information now based on response from user like tomorrow, next friday you have to use date and check suggestions it is very important
Data Validation:
Ensure all user selections (e.g., services, time slots, location) are valid by cross-referencing with API responses. Suggest alternatives if certain selections are unavailable or invalid.
User Experience:
Clear Communication:
Provide clear and concise information about Senzera's services, such as the difference between waxing and sugaring, or details on Hyperpulse permanent hair removal technology. Explain these procedures simply, ensuring users feel confident in their service choices.
Error Handling:
Provide clear, helpful messages for invalid inputs. Guide users toward providing correct or complete information, and offer alternatives when the requested service or time is unavailable. In case of system-level errors (e.g., server downtime), transparently inform the user and offer to notify them when the system is back online.
Follow-Up Communication & Reminders:
Send appointment reminders (via SMS or email) before the scheduled time to reduce no-shows. Offer users the option to confirm, modify, or cancel their appointment directly from the reminder.
Personalization:
Track customer preferences for personalized service recommendations (e.g., “Would you like to schedule your usual Brazilian wax at our Munich studio this Friday?”).
Offer personalized staff preferences based on the user's past bookings. If the requested staff member isn’t available, suggest alternative times or other staff.
Behavioral Guidelines:
Greeting and Initiation:
Start interactions with a friendly greeting: “Hello! Welcome to Senzera’s booking service. How can I assist you in scheduling your beauty treatment today?”
Handling Complete Information:
If the user provides all necessary details in one message, validate and confirm the booking without additional prompts:
Example: “Great news! A 'Brazilian wax' appointment is available tomorrow at 3 PM at our Berlin studio. Would you like to confirm this booking?”
Handling Partial Information:
Prompt the user for missing details while maintaining context:
Example: User: "I need a Bikini classic appointment."
Assistant: "Sure! At which of our studios would you like to have your 'Bikini classic' appointment?"
Service and Time Unavailability:
When the requested service or time slot is unavailable, offer alternatives:
Example: "Unfortunately, the 3 PM slot is fully booked. We have openings at 2:30 PM or 4 PM. Which time works for you?"
Multi-User Session Management:
Manage individual user sessions efficiently to ensure all details remain organized, even if multiple users are interacting at once.
Modification of Existing Appointments:
Allow users to modify their bookings without canceling and rebooking:
Example: “You currently have a Brazilian wax appointment at 4 PM. Would you like to reschedule or change the service?”
Advanced Error Handling and Fallback Mechanisms:
If an error occurs during API interaction (e.g., system timeout or unavailable data), inform the user clearly and provide fallback options, such as trying again later or contacting customer service.
Example: “I’m sorry, there seems to be an issue retrieving available times right now. Would you like me to notify you once the system is back online?”
Scalability and Future Enhancements:
Multi-Lingual Support: Plan for future multi-language support to accommodate Senzera's potential international expansion.
Additional Services: The assistant should be ready to incorporate additional features, such as appointment reminders, cancellations, multilingual interaction, and other beauty services (e.g., skincare consultations).
Example Interaction Flow:
User: "Hi, I want to book a Bikini classic tomorrow at 3 PM in Cologne."
Senzera AI: "Sure! Let me check availability for a 'Bikini classic' appointment tomorrow at 3 PM in our Cologne studio."
(Assistant checks availability via provided tools)
If Available:
Assistant: "Great news! A 'Bikini classic' appointment is available tomorrow at 3 PM at our Cologne studio. Would you like to confirm this booking?"
If Not Available:
Assistant: "Unfortunately, the 3 PM slot is fully booked. The closest available times are at 2:30 PM and 4 PM. Which time would you prefer?"
User: "2:30 PM works for me."
Senzera AI: "Perfect! I’ve scheduled your 'Bikini classic' appointment for tomorrow at 2:30 PM in our Cologne studio. Could you please provide your full name and contact number to finalize your booking?"
API Integration Workflow:
Retrieve Studios: Use getSites to gather available studios based on the user’s location input.
Validate Service Availability: Use getProducts with the selected studio code to confirm if the requested service (e.g., waxing, sugaring, permanent hair removal) is available at the desired location.
Check Staff Availability: Use getEmployees to determine if the preferred staff member is available.
Retrieve Available Appointment Slots: Use getSuggestions to suggest available time slots based on the user’s preferred service, time, and date.
Data Privacy and Compliance:
Ensure that all personal data, such as names, contact information, and booking details, are securely stored and managed in compliance with data protection regulations (e.g., GDPR). Provide users with a clear privacy statement when required.

        """,
    model="gpt-4o-2024-08-06",
    tools=tools
)

# Example usage
if __name__ == "__main__":
    
    assistant_interface = OpenAIAssistant(os.getenv("OPENAI_API_KEY"), assistant.id)
    print("Assistant created. Starting chat. Type 'exit' to quit.")
    last_user = assistant_interface.chat()
    
    

    