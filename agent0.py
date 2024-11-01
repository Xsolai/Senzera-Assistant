import datetime
import time
from openai import OpenAI
import os
import json
from typing import List, Dict, Any, Optional
from appointment_tools import cancel_appointment, confirm_appointment, get_employees, get_sites, get_product, get_suggestions

class AssistantManager:
    def __init__(self, api_key: str, assistant_id: str):
        """Initialize the AssistantManager with API key and assistant ID."""
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.active_thread_id: Optional[str] = None
        self.user_threads: Dict[str, str] = {}  # Store thread IDs for each user
        # self.is_new_conversation = True  # Track if this is a new conversation
    
    def get_or_create_thread(self, user_id: str) -> str:
        """Get existing thread for user or create new one."""
        if user_id not in self.user_threads:
            thread = self.client.beta.threads.create()
            self.user_threads[user_id] = thread.id
        return self.user_threads[user_id]
    
    
    def start_new_conversation(self, user_id: str) -> None:
        """Start a new conversation thread for a specific user."""
        if user_id in self.user_threads:
            try:
                self.client.beta.threads.delete(self.user_threads[user_id])
            except Exception as e:
                print(f"Warning: Could not delete old thread for user {user_id}: {e}")
        
        thread = self.client.beta.threads.create()
        self.user_threads[user_id] = thread.id
        
    def add_message_to_thread(self, user_id: str, question: str) -> None:
        """Add a message to the user's thread."""
        thread_id = self.get_or_create_thread(user_id)
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        question = f"{question}\n\n(Current Date and Time: {current_datetime})"
            
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=question
        )
        
    def handle_tool_calls(self, thread_id: str, run_id: str, tool_calls: List[Dict[Any, Any]], user_id) -> None:
        """Handle tool calls with improved error handling and logging."""
        tool_outputs = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
    
                # Function mapping to make code more maintainable
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
                        # arguments.get('customer_contact'),
                        user_id,
                        arguments.get('city'),
                        arguments.get('service_name'),
                        arguments.get('appointment_date'),
                        arguments.get('appointment_time'),
                        arguments.get('s_card'),
                        # arguments.set('user_id'),
                        # arguments.get('user_id')
                    ),
                    "cancel_appointment": lambda: cancel_appointment(arguments.get('appointment_id'))
                }
                
                if function_name in function_mapping:
                    print(f"Executing {function_name} with arguments: {arguments}")
                    result = function_mapping[function_name]()
                else:
                    result = {"error": f"Function {function_name} not implemented"}
                    print(f"Warning: Unimplemented function called: {function_name}")
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })
                
            except Exception as e:
                print(f"Error in tool call {function_name}: {str(e)}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": str(e)})
                })
        
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )

    def get_latest_assistant_response(self, user_id: str) -> str:
        """Get only the latest assistant response from the user's thread."""
        thread_id = self.user_threads.get(user_id)
        if not thread_id:
            return "No conversation thread found."
            
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=1
        )
        
        for message in messages:
            if message.role == "assistant":
                return message.content[0].text.value
        return "No response from assistant."

    def run_conversation(self, user_id: str, question: str) -> str:
        """Run a conversation turn for a specific user."""
        try:
            # Add the user question to the conversation thread
            self.add_message_to_thread(user_id, question)
            thread_id = self.user_threads.get(user_id)
            
              # Start a new run for the conversation, only if no active run
            run = None
            try:
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=self.assistant_id
                )
            except Exception as e:
                if "run run_" in str(e):
                    # Another run is active; wait or handle it
                    print("An active run is detected, waiting...")
                    time.sleep(2)  # Retry after waiting
                    return self.run_conversation(user_id, question)  # Recursive retry  
            
            # Start a new run for the conversation
            # run = self.client.beta.threads.runs.create(
            #     thread_id=thread_id,
            #     assistant_id=self.assistant_id
            # )   

            timeout = 60 # Max wait time in seconds
            start_time = time.time()

            # Poll the status of the run periodically
            while True:
                if time.time() - start_time > timeout:
                    raise TimeoutError("Conversation run timed out")

                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                # If the run completes, break the loop
                if run.status == "completed":
                    return self.get_latest_assistant_response(user_id)
                
                elif run.status == "requires_action":
                    # Handle tool calls if needed
                    self.handle_tool_calls(
                        thread_id,
                        run.id,
                        run.required_action.submit_tool_outputs.tool_calls,
                        user_id  
                    )
                
                elif run.status in ["failed", "expired", "cancelled"]:
                    # Retry logic for transient issues
                    print(f"Run failed with status: {run.status}. Retrying...")
                    return self.retry_conversation(user_id, question)

                time.sleep(1)

        except TimeoutError as te:
            print(f"Timeout error: {te}")
            return "Sorry, the system is taking too long to respond. Please try again later."

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return "Sorry, I'm having trouble processing your request. Please try again or contact support."

    def retry_conversation(self, user_id: str, question: str) -> str:
        """Retry the conversation once if it fails."""
        try:
            # Retry the conversation only once
            print("Retrying the conversation...")
            return self.run_conversation(user_id, question)
        except Exception as e:
            print(f"Retry failed: {str(e)}")
            return "We're still facing issues. Please try again later or contact support."
        
    # def run_conversation(self, user_id: str, question: str) -> str:
    #     """Run a conversation turn for a specific user."""
    #     try:
    #         self.add_message_to_thread(user_id, question)
    #         thread_id = self.user_threads[user_id]
            
    #         run = self.client.beta.threads.runs.create(
    #             thread_id=thread_id,
    #             assistant_id=self.assistant_id
    #         )

    #         timeout = 300
    #         start_time = time.time()
            
    #         while True:
    #             if time.time() - start_time > timeout:
    #                 raise TimeoutError("Conversation run timed out")
                
    #             run = self.client.beta.threads.runs.retrieve(
    #                 thread_id=thread_id,
    #                 run_id=run.id
    #             )
                
    #             if run.status == "completed":
    #                 break
    #             elif run.status == "requires_action":
    #                 self.handle_tool_calls(
    #                     thread_id,
    #                     run.id,
    #                     run.required_action.submit_tool_outputs.tool_calls
    #                 )
    #             elif run.status in ["failed", "expired", "cancelled"]:
    #                 raise Exception(f"Run failed with status: {run.status}")
                
    #             time.sleep(1)

    #         return self.get_latest_assistant_response(user_id)
            
    #     except Exception as e:
    #         error_message = f"Error in conversation: {str(e)}"
    #         print(error_message)
    #         return error_message
        
def main():
    """Main function with improved error handling and user experience."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
        
    assistant_id = "asst_xDJcDSKfHhjBMracBO9pGWmy"
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