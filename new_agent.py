import datetime
import time
from typing import Any, Dict, List
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

from tools.tools import check_profile, create_profile

load_dotenv()

class AssistantManager:
    def __init__(self, api_key: str, assistant_id: str):
        """Initialize the AssistantManager with API key and assistant ID."""
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.user_threads: Dict[str, str] = {}  # Store thread IDs for each user
        self.active_runs: Dict[str, str] = {}  # Track active runs for each thread

    def get_or_create_thread(self, user_id: str) -> str:
        """Get existing thread for user or create new one."""
        if user_id not in self.user_threads:
            thread = self.client.beta.threads.create()  # Synchronous call
            self.user_threads[user_id] = thread.id
        return self.user_threads[user_id]

    def cleanup_active_run(self, thread_id: str) -> None:
        """Clean up any existing active run for a thread."""
        if thread_id in self.active_runs:
            try:
                run_id = self.active_runs[thread_id]
                run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)  # Synchronous
                if run.status in ["queued", "in_progress", "requires_action"]:
                    self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)  # Synchronous
            except Exception as e:
                print(f"Error cleaning up run: {e}")
            finally:
                del self.active_runs[thread_id]

    def add_message_to_thread(self, user_id: str, question: str) -> None:
        """Add a message to the user's thread with active run check."""
        thread_id = self.get_or_create_thread(user_id)
        self.cleanup_active_run(thread_id)
        
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        question = f"{question}\n\n(Current Date and Time: {current_datetime})"
        
        max_retries = 5
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                self.client.beta.threads.messages.create(thread_id=thread_id, role="user", content=question)  # Synchronous
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} adding message: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise

    def run_conversation(self, user_id: str, question: str) -> str:
        """Run a conversation turn with error handling and run status management."""
        thread_id = self.get_or_create_thread(user_id)
        max_retries = 5
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                self.cleanup_active_run(thread_id)
                time.sleep(1)
                self.add_message_to_thread(user_id, question)
                
                # Start a new run
                run = self.client.beta.threads.runs.create(thread_id=thread_id, assistant_id=self.assistant_id)  # Synchronous
                self.active_runs[thread_id] = run.id
                
                timeout = 100
                start_time = time.time()
                backoff_interval = 1
                max_backoff = 16

                while time.time() - start_time < timeout:
                    run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)  # Synchronous
                    if run.status == "completed":
                        del self.active_runs[thread_id]
                        return self.get_latest_assistant_response(user_id)
                    elif run.status == "requires_action":
                        self.handle_tool_calls(
                            thread_id, run.id, run.required_action.submit_tool_outputs.tool_calls, user_id
                        )
                    elif run.status in ["failed", "expired", "cancelled"]:
                        self.cleanup_active_run(thread_id)
                        break
                    
                    time.sleep(backoff_interval)
                    backoff_interval = min(max_backoff, backoff_interval * 2)  # Exponential backoff

                raise TimeoutError("Conversation run timed out")

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    return f"Sorry, I encountered an error: {str(e)}"

        return "Failed to complete the conversation after multiple attempts."
    
    def handle_tool_calls(self, thread_id: str, run_id: str, tool_calls: List[Dict[Any, Any]], user_id: str) -> None:
        """Handle tool calls with improved error handling."""
        tool_outputs = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                print(f"Function: {function_name} Arguments: {arguments}")
                
                function_mapping = {
                    "create_profile": lambda: create_profile(arguments.get('name'),  user_id, arguments.get('gdpr_consent'), arguments.get('gender')),
                    "check_profile": lambda: check_profile(user_id)
                }
                
                result = function_mapping.get(function_name, lambda: {"error": f"Function {function_name} not implemented"})()
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })
                
            except Exception as e:
                print(f"Error in tool call {tool_call.function.name}: {str(e)}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": str(e)})
                })
        
        try:
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs
            )  # Synchronous
        except Exception as e:
            print(f"Error submitting tool outputs: {e}")

    def get_latest_assistant_response(self, user_id: str) -> str:
        """Get the latest assistant response with error handling."""
        thread_id = self.user_threads.get(user_id)
        if not thread_id:
            return "No conversation thread found."
        
        try:
            messages = self.client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)  # Synchronous
            return next((msg.content[0].text.value for msg in messages if msg.role == "assistant"), "No response from assistant.")
        except Exception as e:
            print(f"Error retrieving assistant response: {e}")
            return "Error retrieving response."

# Test function for basic chatbot interaction
def test_chatbot():
    """Function to test chatbot without any tool integration."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    assistant_id = os.getenv("ASSISTANT_ID")
    assistant_manager = AssistantManager(api_key, assistant_id)

    print("Testing chatbot. Type 'exit' to quit or 'new' to start a new conversation.")

    while True:
        try:
            question = input("\nYou: ").strip()
            if question.lower() == 'exit':
                print("Goodbye!")
                break
            elif question.lower() == 'new':
                assistant_manager.user_threads.clear()
                print("Started new conversation")
                continue
            elif not question:
                continue
            
            response = assistant_manager.run_conversation("123", question)
            print(f"\nAssistant: {response}")
        
        except KeyboardInterrupt:
            print("\nConversation interrupted. Type 'exit' to quit or continue with your next question.")
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("You can continue with your next question or type 'exit' to quit.")

if __name__ == "__main__":
    test_chatbot()
