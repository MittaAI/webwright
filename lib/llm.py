# Openai imports
from openai import AsyncOpenAI

# Anthropic imports
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock, ToolUseBlock

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

from lib.util import custom_style
from lib.util import format_response
from prompt_toolkit.formatted_text import FormattedText

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

def safe_convert_to_dict(content):
    if isinstance(content, dict):
        return {k: safe_convert_to_dict(v) for k, v in content.items()}
    elif isinstance(content, list):
        return [safe_convert_to_dict(item) for item in content]
    elif isinstance(content, (str, int, float, bool, type(None))):
        return content
    else:
        return str(content)
    
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


    def __init__(self, llm="anthropic", config=None):
        self.llm = llm
        self.config = config

    async def call_llm_api(self, messages=None, tools=tools, tool_choice="auto", llm=None, model=None):
        if llm:
            self.llm = llm
        else:
            self.llm = self.config.get_config_value("config", "PREFERRED_API")
        if self.llm == "openai":
            return await self.call_openai_api(messages, tools, tool_choice, model)
        elif self.llm == "anthropic":
            return await self.call_anthropic_api(messages, tools, tool_choice, model)
    
    async def call_anthropic_api(self, messages=None, tools=tools, tool_choice="auto"):
        logger.info("Starting call_anthropic_api method")
        
        # Convert tools to anthropic format
        anthropic_tools = [
            {
                "name": tool['function']['name'],
                "description": tool['function']['description'],
                "input_schema": tool['function']['parameters'],
            } for tool in tools if 'function' in tool
        ] if tools else None

        # Convert messages to anthropic format
        a_messages = []
        id = 0

        for idx, message in enumerate(messages):
            logger.info(f"Processing message {idx}: {json.dumps(message, indent=2)}")
            if message["type"] == "user_query":
                a_messages.append({"role": "user", "content": message["content"]})
            elif message["type"] == "llm_response":
                a_messages.append({"role": "assistant", "content": message["content"]})
            elif message["type"] == "tool_call":
                tool_use_content = {
                    "type": "tool_use",
                    "id": str(id),
                    "name": message["content"]["tool"],
                    "input": json.loads(message["content"]["parameters"])
                }
                a_messages.append({"role": "assistant", "content": [tool_use_content]})
                
                # Safely convert tool result content
                tool_result_content = safe_convert_to_dict(message["content"]["response"])
                logger.info(f"Converted tool result content: {json.dumps(tool_result_content, indent=2)}")
                
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": str(id),
                    "content": tool_result_content
                }
                a_messages.append({"role": "user", "content": [tool_result]})
                id += 1
            else:
                raise ValueError(f"Invalid message type: {message['type']}")

        # Ensure the first message is from the user
        if a_messages and a_messages[0]["role"] != "user":
            a_messages.insert(0, {"role": "user", "content": "Hello, I have a question."})

        # Ensure messages alternate between user and assistant
        cleaned_messages = []
        for i, message in enumerate(a_messages):
            cleaned_messages.append(message)
            if i < len(a_messages) - 1 and message["role"] == a_messages[i+1]["role"]:
                filler_role = "user" if message["role"] == "assistant" else "assistant"
                filler_content = "I understand. Please continue." if filler_role == "assistant" else "Thank you. I have another question."
                cleaned_messages.append({"role": filler_role, "content": filler_content})

        logger.info(f"Final messages to be sent to API: {json.dumps(cleaned_messages, indent=2)}")

        # Call anthropic API
        client = AsyncAnthropic(api_key=self.config.get_anthropic_api_key())
        try:
            response = await client.messages.create(
                model=self.config.get_config_value("config", "ANTHROPIC_MODEL"),
                max_tokens=2048,
                messages=cleaned_messages,
                tools=anthropic_tools,
                system=SYSTEM_PROMPT
            )
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            logger.error(f"Messages sent to API: {json.dumps(cleaned_messages, indent=2)}")
            raise

        # Extract content, timestamp, and function calls from the response
        text_content = ""
        function_calls = []
        timestamp = datetime.now().isoformat()

        for content_item in response.content:
            if isinstance(content_item, TextBlock):
                text_content += content_item.text
            elif isinstance(content_item, ToolUseBlock):
                function_calls.append({
                    "name": content_item.name,
                    "parameters": content_item.input,
                })

        logger.info(f"Response received: {text_content}")
        logger.info(f"Function calls: {json.dumps(function_calls, indent=2)}")

        # Print the response
        if text_content:
            formatted_response = format_response(text_content)
            print_formatted_text(formatted_response, style=custom_style)

        # Return in the standardized format
        return {
            "content": text_content,
            "timestamp": timestamp,
            "function_calls": function_calls
        }

    async def call_openai_api(self, messages=None, tools=tools, tool_choice="auto", model = None):
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

        # If not model is provided, use the config value
        # If the model contains "o1", do not include tools or tool_choice
        if not model:
            model = self.config.get_config_value("config", "OPENAI_MODEL")

        # Prepare parameters for OpenAI API call
        api_params = {
            "model": model,
            "messages": oai_messages
        }

        # Add system prompt
        if "o1" not in model:
            oai_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
            api_params["tools"] = tools
            api_params["tool_choice"] = tool_choice

        logger.info(oai_messages)

        # Call OpenAI API
        client = AsyncOpenAI(api_key=self.config.get_openai_api_key())
        response = await client.chat.completions.create(**api_params)

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
        if content:
          print()
          formatted_response = format_response(content)
          print_formatted_text(formatted_response, style=custom_style)

        # Return in the standardized format
        return {
            "content": content,
            "timestamp": timestamp,
            "function_calls": function_calls
        }

