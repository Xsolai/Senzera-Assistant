import time
from openai import OpenAI
import os
import json
from typing import List, Dict, Any
from v1.appointment_tools import cancel_appointment, confirm_appointment, get_employees, get_sites, get_product, get_suggestions #, get_employees, get_products, get_product, book_appointment


class AssistantManager:
    def __init__(self, api_key: str, assistant_id: str):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id

    def create_thread_with_question(self, question: str) -> str:
        thread = self.client.beta.threads.create(
            messages=[{
                "role": "user",
                "content": question
            }]
        )
        return thread.id

    def handle_tool_calls(self, thread_id: str, run_id: str, tool_calls: List[Dict[Any, Any]]) -> None:
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            # print(function_name)
            arguments = json.loads(tool_call.function.arguments)
            
            # Handle different tool types
            output = None
            if function_name == "get_sites":
                print(f"get_sites called: {arguments.get('city')}")
                result = get_sites(arguments.get('city'))

            elif function_name == "get_product":
                print(f"get_product called: {arguments.get('city'), arguments.get('service_name')}")
                result = get_product(arguments.get('city'), arguments.get('service_name'))

            elif function_name == "get_employees":
                print(f"get_employees called: {arguments.get('city'), arguments.get('service_name'), arguments.get('appointment_date'), arguments.get('appointment_time')}")
                result = get_employees(arguments.get('city'), arguments.get('service_name'), arguments.get('appointment_date'), arguments.get('appointment_time'))

            elif function_name == "get_suggestions":
                print(f"get_suggestions called: {arguments.get('city'), arguments.get('service_name'), arguments.get('date')}")
                result = get_suggestions(arguments.get('city'), arguments.get('service_name'), arguments.get('date'))

            elif function_name == "confirm_appointment":
                print(f"Confirm Appointment Called: {arguments.get('customer_name'), arguments.get('customer_contact'), arguments.get('city'), arguments.get('service_name'), arguments.get('appointment_date'), arguments.get('appointment_time'), arguments.get('price_category')}")
                result = confirm_appointment(
                    arguments.get('customer_name'),
                    arguments.get('customer_contact'),
                    arguments.get('city'),
                    arguments.get('service_name'),
                    arguments.get('appointment_date'),
                    arguments.get('appointment_time'),
                    arguments.get('price_category')
                )

            elif function_name == "cancel_appointment":
                print(f"cancel_appointment called: {arguments.get('appointment_id')}")
                result = cancel_appointment(arguments.get('appointment_id'))

            else:
                result = f"Function {function_name} not implemented"

            # if function_name == "get_current_weather":
            #     output = self.get_weather(function_args.get("location"))
            # elif function_name == "get_stock_price":
            #     output = self.get_stock_price(function_args.get("symbol"))
            # elif function_name == 'current_time':
            #     print(function_args)
            #     output = self.get_current_time()
            # Add more tool handlers as needed
            
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result)
            })
        
        # Submit tool outputs back to the assistant
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )

    def run_conversation(self, question: str) -> List[Dict[str, str]]:
        # Create thread with initial question
        thread_id = self.create_thread_with_question(question)
        
        # Create run
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )

        # Monitor run status
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run.status == "completed":
                break
            elif run.status == "requires_action":
                # Handle tool calls
                self.handle_tool_calls(
                    thread_id,
                    run.id,
                    run.required_action.submit_tool_outputs.tool_calls
                )
            elif run.status in ["failed", "expired"]:
                raise Exception(f"Run failed with status: {run.status}")
            
            time.sleep(1)

        # Retrieve and return messages
        messages = self.client.beta.threads.messages.list(thread_id)
        return [
            {
                "role": msg.role,
                "content": msg.content[0].text.value
            }
            for msg in messages
        ]


# Usage example
def main():
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = "asst_xDJcDSKfHhjBMracBO9pGWmy"
    
    assistant_manager = AssistantManager(api_key, assistant_id)
    
    while True:
        try:
            question = input("Ask your question (or type 'exit' to quit): ")
            if question.lower() == 'exit':
                print("Exiting the conversation. Goodbye!")
                break

            messages = assistant_manager.run_conversation(question)
            for message in messages:
                print(f"{message['role']}: {message['content']}")
        
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()