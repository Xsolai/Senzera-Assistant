import datetime
import time
from openai import OpenAI
import os
import json
from typing import List, Dict, Any, Optional
from appointment_tools import cancel_appointment, confirm_appointment, fetch_my_appointments, get_employees, get_sites, get_product, get_suggestions

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
            thread = self.client.beta.threads.create()
            self.user_threads[user_id] = thread.id
        return self.user_threads[user_id]
    
    def cleanup_active_run(self, thread_id: str) -> None:
        """Clean up any existing active run for a thread."""
        if thread_id in self.active_runs:
            try:
                run_id = self.active_runs[thread_id]
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status in ["queued", "in_progress", "requires_action"]:
                    self.client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run_id
                    )
            except Exception as e:
                print(f"Error cleaning up run: {e}")
            finally:
                del self.active_runs[thread_id]
    
    def add_message_to_thread(self, user_id: str, question: str) -> None:
        """Add a message to the user's thread with active run check."""
        thread_id = self.get_or_create_thread(user_id)
        
        # Clean up any existing active run
        self.cleanup_active_run(thread_id)
        
        # Add the message
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        question = f"{question}\n\n(Current Date and Time: {current_datetime})"
        
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=question
                )
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} adding message: {e}")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def run_conversation(self, user_id: str, question: str) -> str:
        """Run a conversation turn with enhanced error handling and run status management."""
        thread_id = self.get_or_create_thread(user_id)
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # First, ensure no active runs exist
                self.cleanup_active_run(thread_id)
                
                # Wait a moment to ensure cleanup is complete
                time.sleep(1)
                
                # Add message to thread with verification
                try:
                    self.add_message_to_thread(user_id, question)
                except Exception as e:
                    print(f"Error adding message: {e}")
                    if "while a run is active" in str(e):
                        # Wait longer if there's still an active run
                        time.sleep(5)
                        self.cleanup_active_run(thread_id)
                        time.sleep(1)
                        self.add_message_to_thread(user_id, question)
                    else:
                        raise
                
                # Create new run with verification
                try:
                    run = self.client.beta.threads.runs.create(
                        thread_id=thread_id,
                        assistant_id=self.assistant_id
                    )
                    self.active_runs[thread_id] = run.id
                except Exception as e:
                    if "while a run is active" in str(e):
                        # Wait and retry if there's a lingering run
                        time.sleep(5)
                        self.cleanup_active_run(thread_id)
                        time.sleep(1)
                        run = self.client.beta.threads.runs.create(
                            thread_id=thread_id,
                            assistant_id=self.assistant_id
                        )
                        self.active_runs[thread_id] = run.id
                    else:
                        raise
                
                # Wait for run completion with enhanced status checking
                timeout = 60  # Max wait time in seconds
                start_time = time.time()
                status_check_retries = 3
                
                while True:
                    if time.time() - start_time > timeout:
                        self.cleanup_active_run(thread_id)
                        raise TimeoutError("Conversation run timed out")
                    
                    # Retrieve run status with retries
                    run_status = None
                    for status_attempt in range(status_check_retries):
                        try:
                            run = self.client.beta.threads.runs.retrieve(
                                thread_id=thread_id,
                                run_id=run.id
                            )
                            run_status = run.status
                            break
                        except Exception as e:
                            if status_attempt == status_check_retries - 1:
                                raise
                            time.sleep(1)
                    
                    if run_status == "completed":
                        if thread_id in self.active_runs:
                            del self.active_runs[thread_id]
                        return self.get_latest_assistant_response(user_id)
                    
                    elif run_status == "requires_action":
                        try:
                            self.handle_tool_calls(
                                thread_id,
                                run.id,
                                run.required_action.submit_tool_outputs.tool_calls,
                                user_id
                            )
                        except Exception as e:
                            print(f"Error in tool calls: {e}")
                            # Don't immediately fail - let the run continue
                            time.sleep(1)
                            continue
                    
                    elif run_status in ["failed", "expired", "cancelled"]:
                        self.cleanup_active_run(thread_id)
                        if attempt < max_retries - 1:
                            print(f"Run failed with status: {run_status}. Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                            break
                        else:
                            raise Exception(f"Run failed after {max_retries} attempts with status: {run_status}")
                    
                    elif run_status == "queued":
                        # Wait longer for queued status
                        time.sleep(2)
                        continue
                    
                    elif run_status == "in_progress":
                        # Normal progress, shorter wait
                        time.sleep(1)
                        continue
                    
                    else:
                        # Unknown status
                        print(f"Unknown run status: {run_status}")
                        time.sleep(1)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
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
                customer_contact = user_id
                arguments['user_id'] = user_id
                function_mapping = {
                    "get_sites": lambda: get_sites(arguments.get('city')),
                    "get_product": lambda: get_product(arguments.get('city'), arguments.get('service_name')),
                    "get_employees": lambda: get_employees(
                        arguments.get('city'),
                        arguments.get('service_name'),
                        arguments.get('appointment_date'),
                        arguments.get('appointment_time')
                    ),
                    "get_suggestions": lambda: get_suggestions(
                        arguments.get('city'),
                        arguments.get('service_name'),
                        arguments.get('date'),
                        arguments.get('time')
                    ),
                    "confirm_appointment": lambda: confirm_appointment(
                        arguments.get('customer_name'),
                        customer_contact,
                        arguments.get('city'),
                        arguments.get('service_name'),
                        arguments.get('appointment_date'),
                        arguments.get('appointment_time'),
                        arguments.get('s_card'),
                        user_id
                        
                    ),
                    "cancel_appointment": lambda: cancel_appointment(arguments.get('appointment_id'),user_id),
                    "fetch_my_appointments": lambda: fetch_my_appointments(user_id)
                }
                
                if function_name in function_mapping:
                    result = function_mapping[function_name]()
                else:
                    result = {"error": f"Function {function_name} not implemented"}
                
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
            )
        except Exception as e:
            print(f"Error submitting tool outputs: {e}")
            raise

    def get_latest_assistant_response(self, user_id: str) -> str:
        """Get the latest assistant response with error handling."""
        thread_id = self.user_threads.get(user_id)
        if not thread_id:
            return "No conversation thread found."
        
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=1
            )
            
            for message in messages:
                if message.role == "assistant":
                    return message.content[0].text.value
            return "No response from assistant."
            
        except Exception as e:
            print(f"Error retrieving assistant response: {e}")
            return "Error retrieving response."


def main():
    """Main function with improved error handling and user experience."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
        
    assistant_id = os.getenv("ASSITANT_ID")
    assistant_manager = AssistantManager(api_key, assistant_id)
    
    print("Starting new conversation. Type 'exit' to quit or 'new' to start a new conversation.")
    
    while True:
        try:
            question = input("\nYou: ").strip()
            
            if question.lower() == 'exit':
                print("Goodbye!")
                break
            elif question.lower() == 'new':
                assistant_manager.start_new_conversation()
                print("Started new conversation")
                continue
            elif not question:
                continue
                
            response = assistant_manager.run_conversation(question)
            print(f"\nAssistant: {response}")
        
        except KeyboardInterrupt:
            print("\nConversation interrupted. Type 'exit' to quit or continue with your next question.")
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("You can continue with your next question or type 'exit' to quit.")

if __name__ == "__main__":
    main()