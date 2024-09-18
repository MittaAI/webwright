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
You are an intelligent assistant that helps users accomplish tasks efficiently. Follow these guidelines:

1. Analyze the user's request and break it down into executable steps.
2. Provide a concise overview of your planned steps, including the specific functions you intend to call.
3. Pause between function executions to ask the user for confirmation before proceeding, especially when modifying files or executing commands.
4. After executing a function, explain what was done.
5. Before executing any Docker commands, including starting containers, you must first use the 'search_file' function to look for 'Dockerfile' and 'docker-compose.yml' files in the project directory. Only proceed with Docker operations if these files are found.
6. Minimize the number of function calls while ensuring task completion.
7. If you search for a file, or search for memories (through search), you should probably tell the user what you are going to do next.
8. If you don't know what the user is talking about, or don't have any information about the matter, use the search function to search for different keyterms that may be related to what they are saying, or what is in your short term memory.
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

    async def call_llm_api(self, messages=None, tools=tools, tool_choice="auto", service_api=None, model=None):
        if service_api:
            self.service_api = service_api
        else:
            self.service_api = self.config.get_config_value("config", "PREFERRED_API")
        if self.service_api == "openai":
            return await self.call_openai_api(messages, tools, tool_choice, model)
        elif self.service_api == "anthropic":
            return await self.call_anthropic_api(messages, tools, tool_choice, model)
    
    async def call_anthropic_api(self, messages=None, tools=tools, tool_choice="auto", model=None):  
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
            # logger.info(f"Processing message {idx}: {json.dumps(message, indent=2)}")
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
                logger.info(f"Ignoring bad message type: {message['type']}")

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

        # logger.info(f"Final messages to be sent to API: {json.dumps(cleaned_messages, indent=2)}")

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

        # Remove the print_formatted_text call
        formatted_response = None
        if text_content:
            formatted_response = format_response(text_content)

        # Return in the standardized format, including the formatted_response
        return {
            "content": text_content,
            "timestamp": timestamp,
            "function_calls": function_calls,
            "formatted_response": formatted_response
        }

    async def call_openai_api(self, messages=None, tools=tools, tool_choice="auto", model=None):
        # Convert messages to OpenAI's format
        oai_messages = []
        for message in messages:
            if message["type"] == "user_query":
                oai_messages.append({"role": "user", "content": message["content"]})
            elif message["type"] == "llm_response":
                oai_messages.append({"role": "assistant", "content": message["content"]})
            elif message["type"] == "tool_call" and "o1" not in model:
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
            elif "o1" not in model:
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
        logger.info(api_params)
        # Add system prompt
        if "o1" not in model:
            oai_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
            api_params["tools"] = tools
            api_params["tool_choice"] = tool_choice
            
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

        # Remove the print_formatted_text call
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

