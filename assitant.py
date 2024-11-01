import os
from agent import AssistantManager
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set")


assistant_id = os.getenv("ASSITANT_ID")
assistant_manager = AssistantManager(api_key, assistant_id)

def get_response_from_gpt(msg, user_id):
    response = assistant_manager.run_conversation(user_id, msg)
    print(f"Response for user {user_id}: {response}")
    return response