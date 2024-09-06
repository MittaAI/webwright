from openai import AsyncOpenAI

# Utility imports (assuming these are from your local modules)
from lib.util import create_and_check_directory
from prompt_toolkit import PromptSession, print_formatted_text
from lib.util import get_logger
from lib.util import setup_function_logging

# Import helper functions and decorators
from lib.function_wrapper import function_info_decorator, tools, callable_registry
from git import Repo

import json
from datetime import datetime

# Configure logging
logger = get_logger()

SYSTEM_PROMPT = """
You are an intelligent assistant that helps users accomplish their tasks efficiently. Follow these guidelines:

1. Analyze the user's request and break it down into executable steps.
2. Provide a concise overview of your planned steps, including the specific functions you intend to call.
3. Execute the necessary functions to complete the task.
4. Minimize the number of function calls while ensuring task completion.
5. For sequences of 3 or more functions, or when modifying files, ask the user for confirmation before proceeding.
6. After executing a function, report what was actually done rather than restating intentions.

Example interaction:

User: Analyze the performance of our data processing script and suggest improvements.

Assistant: To accomplish this task, I plan to:

1. Read the current script using 'read_file'.
2. Analyze the script's content for performance bottlenecks.
3. Create an optimized version using 'write_file'.
4. Execute both versions with 'execute_script' to compare performance.

This plan involves reading, writing, and executing files. Shall I proceed?

User: Yes, go ahead.

Assistant: Thank you for the confirmation. I'll proceed with the plan.

1. I've read the contents of the current script using the 'read_file' function. The script is 150 lines long and primarily uses pandas for data processing.

2. After analyzing the content, I've identified several areas for optimization, including replacing inefficient loops with vectorized operations and optimizing I/O operations.

3. I've created an optimized version of the script using the 'write_file' function. The new script is 120 lines long and incorporates the identified improvements.

4. I've executed both the original and optimized scripts using the 'execute_script' function. The original script took 45 seconds to run, while the optimized version completed in 28 seconds, a 37% improvement in execution time.

Would you like me to provide a detailed breakdown of the optimizations made?
"""

class llm_wrapper:
    """
    Takes in a list of messages in the omnilog format:
      {
        content: the message content in string format, if function call includes the function name and the results
        timestamp: the timestamp in string format,
        type: the type of message in string format. One of the following: "tool_call", "llm_response", "user_query"
      }
    Calls the selected API with the messages. Prints the streamed response to terminal and returns the response in the following format:
      {
        content: the response text in string format
        timestamp: the timestamp in string format,
        function_calls: a list of function calls in the following format: {"name": function name, "parameters": dictionary of argument name and its value}
      }
    """


    def __init__(self):
        self.llm = "openai"

    async def call_llm_api(self, messages=None, config=None, tools=tools, tool_choice="auto"):
        if self.llm == "openai":
            return await self.call_openai_api(messages, config, tools, tool_choice)
    
    async def call_openai_api(self, messages=None, config=None, tools=tools, tool_choice="auto"):
            # Convert messages to OpenAI's format
            oai_messages = []
            for message in messages:
                if message["type"] == "user_query":
                    oai_messages.append({"role": "user", "content": message["content"]})
                elif message["type"] == "llm_response":
                    oai_messages.append({"role": "assistant", "content": message["content"]})
                elif message["type"] == "tool_call":
                    # {'role': 'assistant', 'content': None, 'function_call': {'name': 'cat_file', 'arguments': '{"file_path": "/Users/andylegrand/Desktop/untitled folder/diff.txt"}'}},
                    # {'role': 'function', 'name': 'cat_file', 'content': '{"success": true, "contents": "<returned values>")"}'}]
                    oai_messages.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": message["content"]["tool"],
                            "arguments": json.dumps(message["content"]["parameters"])
                        }
                    })
                    oai_messages.append({
                        "role": "function",
                        "name": message["content"]["tool"],
                        "content": message["content"]["response"]
                    })
                else:
                    raise ValueError(f"Invalid message type: {message['type']}")

            #print(oai_messages)

            # Add system prompt
            oai_messages.append({"role": "system", "content": SYSTEM_PROMPT})

            # Call OpenAI API
            client = AsyncOpenAI(api_key=config.get_openai_api_key())
            response = await client.chat.completions.create(
                model=config.get_config_value("config", "OPENAI_MODEL"),
                messages=oai_messages,
                tools=tools,
                tool_choice=tool_choice
            )

            # Extract content, timestamp, and function calls from the response
            assistant_message = response.choices[0].message
            content = assistant_message.content
            timestamp = datetime.now().isoformat()
            function_calls = []

            # Processing potential function/tool calls in the response
            if assistant_message.tool_calls:
                function_calls = []
                for tool_call in assistant_message.tool_calls:
                    try:
                      function_calls.append({
                        "name": tool_call.function.name,
                        "parameters": json.loads(tool_call.function.arguments),
                      })
                    except Exception as e:
                      print(f"Failed to process tool call: {tool_call}")
                      print(f"Error: {e}")

            # Print the response
            print(content)

            # Return in the standardized format
            return {
                "content": content,
                "timestamp": timestamp,
                "function_calls": function_calls
            }

