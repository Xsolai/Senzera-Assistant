import time
import openai
from openai import OpenAI
import os


question = ("Tell me time right now?")

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
my_assistant = client.beta.assistants.retrieve("asst_xDJcDSKfHhjBMracBO9pGWmy")

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": question
        }
    ]
)


run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=my_assistant.id
)

while run.status != 'completed':
    run = client.beta.threads.runs.retrieve(
      thread_id=thread.id,
      run_id=run.id
    )
    print(run.status)
    time.sleep(5)


thread_messages = client.beta.threads.messages.list(thread.id)

# Define a custom tool function (example: Fetch current time)
def get_current_time():
    print("Get Current Time Called")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# Define a tool dictionary to map tool calls
tools = {
    "current_time": get_current_time  # Example of a custom tool
}
# Process the thread messages to detect if a tool is needed
for message in thread_messages:
    print(message['role'] + ": " + message['content'])
    
    # Check if the assistant requests a tool call
    if 'tool' in message['content']:
        tool_name = message['content'].split(":")[-1].strip()
        
        if tool_name in tools:
            # Call the corresponding tool function
            tool_result = tools[tool_name]()
            print(f"Tool '{tool_name}' executed: {tool_result}")
            
            # Send the tool result back to the assistant
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"The result of {tool_name} is: {tool_result}"
            )

# Final message retrieval to show the updated conversation
thread_messages = client.beta.threads.messages.list(thread.id)
for message in thread_messages:
    print(message['role'] + ": " + message['content'])