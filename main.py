import os
import threading
from twilio.rest import Client
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from threading import Thread
from assitant import get_response_from_gpt
from fastapis import run_fastapi

# Load environment variables from .env file
load_dotenv()

class WhatsAppHandler:
    def __init__(self):
        """
        Initializes the WhatsAppHandler with Twilio credentials loaded from environment variables.
        """
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.messaging_service_sid = os.getenv('TWILIO_MESSAGING_SERVICE_SID')  # Load Messaging Service SID
        self.from_number=os.getenv('TWILIO_WHATSAPP_NUMBER')
        self.client = Client(self.account_sid, self.auth_token)

    def send_message(self, to_number, message_body):
        """
        Sends a WhatsApp message using Twilio API and Messaging Service SID.
        
        :param to_number: Receiver's phone number (format: +recipient_number).
        :param message_body: The message you want to send.
        :return: The message SID.
        """
        message = self.client.messages.create(
            body=message_body,
            messaging_service_sid=self.messaging_service_sid,
            from_=self.from_number,
            to=to_number
        )
        print(f"Message sent: {message.status}")
        return message.sid

    def start_incoming_listener(self, host="0.0.0.0", port=5000):
        """
        Starts a Flask server to listen for incoming WhatsApp messages.
        
        :param host: The host IP address.
        :param port: The port number to listen on.
        """
        app = Flask(__name__)

        @app.route('/incoming-whatsapp', methods=['POST'])
        def receive_message():
            """
            Webhook to receive WhatsApp messages via Twilio.
            Responds with the same message text (echo).
            """
            incoming_msg = request.values.get('Body', '').lower()  # The incoming message body
            sender_number = request.values.get('From', '')  # Sender's WhatsApp number

            # Log the incoming message
            print(f"Message received from {sender_number}: {incoming_msg}")
            number = ''.join(filter(str.isdigit, sender_number))
            #Give msg from here to groq
            response=get_response_from_gpt(incoming_msg, number)
            #send response back to incoming msg
            # Create a response that echoes the incoming message
            resp = MessagingResponse()
            resp.message(response)  # Respond with the same message text

            return str(resp) # Respond to Twilio's webhook with the message

        print(f"Starting WhatsApp listener on {host}:{port}...")
        app.run(host=host, port=port)
        

if __name__  == '__main__':
    
    # Initialize the handler
    whatsapp_handler = WhatsAppHandler()

    # Start Flask and FastAPI servers in separate threads
    flaskapp_thread = Thread(target=whatsapp_handler.start_incoming_listener, kwargs={"host": "0.0.0.0", "port": 5000})
    fastapi_thread = Thread(target=run_fastapi)
    
    # Start the threads
    flaskapp_thread.start()
    # fastapi_thread.start()

    # Wait for both threads to complete
    flaskapp_thread.join()
    # fastapi_thread.join()
