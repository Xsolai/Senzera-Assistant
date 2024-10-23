import os
from main import OpenAIAssistant, assistant

assistant_interface = OpenAIAssistant(os.getenv("OPENAI_API_KEY"), assistant.id)

def get_response_from_gpt(msg):
    
    respone = assistant_interface.process_input(msg)
    return respone