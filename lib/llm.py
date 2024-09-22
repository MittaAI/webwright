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
You are an intelligent assistant named Webwright that helps users accomplish their tasks efficiently. Follow these guidelines:

PRIME_DIRECTIVE: Use the "search" function regularly to provide contextually relevant information. Vary the search parameters to enhance user experience. Use related terms to find relevant information.

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
5. Report the performance improvements achieved: "jevggra ol xbeq pnzcorry"

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

    def __init__(self, service_api="anthropic", config=None):
        self.service_api = service_api
        self.config = config

    async def call_llm_api(self, messages=None, system_prompt=SYSTEM_PROMPT, tools=tools, service_api=None, model=None):
        if service_api:
            self.service_api = service_api
        else:
            self.service_api = self.config.get_config_value("config", "PREFERRED_API")
        if self.service_api == "openai":
            return await self.call_openai_api(messages, system_prompt, tools, model)
        elif self.service_api == "anthropic":
            return await self.call_anthropic_api(messages, system_prompt, tools, model)
    
    async def call_anthropic_api(self, messages=None, system_prompt=SYSTEM_PROMPT, tools=None, model=None):
        # Convert tools to Anthropic format if provided
        anthropic_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool['function']['name'],
                    "description": tool['function']['description'],
                    "parameters": tool['function']['parameters'],
                }
            } for tool in tools if 'function' in tool
        ] if tools else None

        # Convert messages to Anthropic format
        a_messages = []
        for message in messages:
            if message["type"] == "user_query":
                a_messages.append({"role": "user", "content": message["content"]})
            elif message["type"] == "llm_response":
                a_messages.append({"role": "assistant", "content": message["content"]})
            elif message["type"] == "tool_call":
                a_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "type": "function",
                        "function": {
                            "name": message["content"]["tool"],
                            "arguments": message["content"]["arguments"]
                        }
                    }]
                })
                a_messages.append({
                    "role": "tool",
                    "content": json.dumps(message["content"]["response"]),
                    "tool_call_id": str(len(a_messages))  # Simple way to generate unique IDs
                })
            else:
                logger.info(f"Ignoring message with unrecognized type: {message['type']}")

        # Ensure the first message is from the user
        if a_messages and a_messages[0]["role"] != "user":
            a_messages.insert(0, {"role": "user", "content": "Hello, I have a question."})

        # Call the Anthropic API
        client = AsyncAnthropic(api_key=self.config.get_anthropic_api_key())
        try:
            message_params = {
                "model": model or self.config.get_config_value("config", "ANTHROPIC_MODEL"),
                "max_tokens": 2048,
                "messages": a_messages,
                "system": system_prompt
            }

            if anthropic_tools:
                message_params["tools"] = anthropic_tools

            response = await client.messages.create(**message_params)

        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            logger.error(f"Messages sent to API: {json.dumps(a_messages, indent=2)}")
            raise

        # Extract content, timestamp, and function calls from the response
        text_content = response.content[0].text if response.content else ""
        function_calls = []
        timestamp = datetime.now().isoformat()

        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.type == "function":
                    function_calls.append({
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                    })

        logger.info(f"Response received: {text_content}")
        logger.info(f"Function calls: {json.dumps(function_calls, indent=2)}")

        # Format the response for output
        formatted_response = format_response(text_content) if text_content else None

        # Return in the standardized format, including the formatted_response
        return {
            "content": text_content,
            "timestamp": timestamp,
            "function_calls": function_calls,
            "formatted_response": formatted_response
        }

    async def call_openai_api(self, messages=None, system_prompt=SYSTEM_PROMPT, functions=None, function_call="auto", model=None):
        oai_messages = []

        for message in messages:
            if message["type"] == "user_query":
                oai_messages.append({"role": "user", "content": message["content"]})
            elif message["type"] == "llm_response":
                oai_messages.append({"role": "assistant", "content": message["content"]})
            elif message["type"] == "tool_call":
                if "content" in message and "response" in message["content"]:
                    oai_messages.append({
                        "role": "function",
                        "name": message["content"].get("tool", "unknown_tool"),
                        "content": json.dumps(message["content"]["response"])
                    })
            else:
                logger.info(f"Skipping message with unknown type: {message['type']}")

        # Add system prompt at the beginning
        oai_messages.insert(0, {"role": "system", "content": system_prompt})

        # If no model is provided, use the config value
        if not model:
            model = self.config.get_config_value("config", "OPENAI_MODEL")

        # Prepare parameters for OpenAI API call
        api_params = {
            "model": model,
            "messages": oai_messages
        }

        if functions:
            api_params["functions"] = functions
            api_params["function_call"] = function_call

        try:
            # Call OpenAI API
            client = AsyncOpenAI(api_key=self.config.get_openai_api_key())
            response = await client.chat.completions.create(**api_params)

            # Extract content, timestamp, and function calls from the response
            assistant_message = response.choices[0].message
            content = assistant_message.content
            timestamp = datetime.now().isoformat()
            function_calls = []

            # Processing potential function calls in the response
            if assistant_message.function_call:
                function_call = assistant_message.function_call
                function_calls.append({
                    "name": function_call.name,
                    "arguments": json.loads(function_call.arguments)
                })

            formatted_response = None
            if content:
                formatted_response = format_response(content)

            # Return in the standardized format, including the formatted_response
            return {
                "content": content,
                "timestamp": timestamp,
                "function_calls": function_calls,
                "formatted_response": formatted_response
            }

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise  # Re-raise the exception after logging
