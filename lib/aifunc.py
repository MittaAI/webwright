import json
import os
import asyncio
from tenacity import retry, wait_random_exponential, stop_after_attempt
from halo import Halo

# OpenAI imports
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

from lib.util import custom_style
from prompt_toolkit.formatted_text import FormattedText


# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Configure logging
logger = get_logger()

# Storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

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

async def execute_function_by_name(function_name, **kwargs):
    logger.info(f"Calling {function_name} with arguments {kwargs}")
    
    if function_name not in callable_registry:
        logger.error(f"Function {function_name} not found in registry")
        return json.dumps({"error": f"Function {function_name} not found in registry"})
    
    try:
        func_logger = setup_function_logging(function_name)
        func_logger.info(f"Function {function_name} called with arguments: {kwargs}")
        function_to_call = callable_registry[function_name]
        
        if asyncio.iscoroutinefunction(function_to_call):
            # If it's a coroutine function, await it
            result = await function_to_call(**kwargs)
        else:
            # If it's a regular function, run it in a thread to avoid blocking
            result = await asyncio.to_thread(function_to_call, **kwargs)
        
        func_logger.info(f"Function {function_name} executed successfully with result: {result}")
        return json.dumps(result) if not isinstance(result, str) else result
    
    except Exception as e:
        func_logger.error(f"Function {function_name} failed with error: {e}")
        return json.dumps({"error": str(e)})

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def openai_chat_completion_request(messages=None, config=None, tools=None, tool_choice="auto"):
    client = AsyncOpenAI(api_key=config.get_openai_api_key())

    if tools:
        function_names = [tool['function']['name'] for tool in tools]
        logger.info("Available OpenAI functions: %s", function_names)

    messages.append({
      "role": "system",
      "content": SYSTEM_PROMPT
    })

    try:
        response = await client.chat.completions.create(
            model=config.get_config_value("config", "OPENAI_MODEL"),
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )
        return response
    except Exception as e:
        logger.error("Unable to generate OpenAI ChatCompletion response: %s", e)
        raise

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def anthropic_chat_completion_request(messages=None, config=None, tools=None):
    client = AsyncAnthropic(api_key=config.get_anthropic_api_key())
    
    if tools:
        anthropic_tools = []
        for tool in tools:
            if 'function' in tool:
                anthropic_tools.append({
                    "name": tool['function']['name'],
                    "description": tool['function']['description'],
                    "input_schema": tool['function']['parameters'],
                })
            else:
                anthropic_tools.append(tool)
        
        function_names = [tool['name'] for tool in anthropic_tools]
    else:
        anthropic_tools = None

    try:
        response = await client.messages.create(
            model=config.get_config_value("config", "ANTHROPIC_MODEL"),
            max_tokens=2048,
            messages=messages,
            tools=anthropic_tools,
            system=SYSTEM_PROMPT
        )
        return response
    except Exception as e:
        logger.error("Unable to generate Anthropic ChatCompletion response: %s", e)
        raise

async def ai(username="anonymous", query="help", config=None, upload_dir=UPLOAD_DIR, history=None):
    text_content = ""
    
    api_to_use = config.get_config_value("config", "PREFERRED_API")
    if api_to_use not in ["openai", "anthropic"]:
        raise ValueError("api_to_use must be either 'openai' or 'anthropic'")
    
    user_dir = os.path.join(upload_dir, username)
    create_and_check_directory(user_dir)
    
    if history is None:
        history = []

    messages = history

    logger.info(f"Initial length of messages: {len(messages)}")
    total_characters = sum(len(message['content']) for message in messages if 'content' in message and message['content'] is not None)
    logger.info(f"Total characters in all messages: {total_characters}")

    max_function_calls = 6
    function_call_count = 0
    
    while function_call_count < max_function_calls:
        spinner = Halo(text='Calling the model...', spinner='dots')
        spinner.start()
        
        if api_to_use == "openai":
            chat_response = await openai_chat_completion_request(messages=messages, config=config, tools=tools)

            if not chat_response:
                spinner.stop()
                return False, {"error": "Failed to get a response from OpenAI"}
            assistant_message = chat_response.choices[0].message
            
            if assistant_message.tool_calls:
                function_calls = []
                for tool_call in assistant_message.tool_calls:
                    try:
                      function_calls.append({
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                        "id": tool_call.id
                      })
                    except Exception as e:
                      print(f"Failed to process tool call: {tool_call}")
                      print(f"Error: {e}")
            else:
                spinner.stop()
                return True, {"response": assistant_message.content}
        
        else:  # Anthropic
            chat_response = await anthropic_chat_completion_request(messages=messages, config=config, tools=tools)
            if not chat_response:
                spinner.stop()
                return False, {"error": "Failed to get a response from Anthropic"}
            
            logger.info(f"Anthropic response: {chat_response}")
            
            function_calls = []

            for content_item in chat_response.content:
                if isinstance(content_item, TextBlock):
                    text_content += content_item.text
                elif isinstance(content_item, ToolUseBlock):
                    function_calls.append({
                        "name": content_item.name,
                        "arguments": content_item.input,
                        "id": content_item.id
                    })

            logger.info(f"Extracted function calls: {function_calls}")
            logger.info(f"Extracted text content: {text_content}")

            if not function_calls:
                spinner.stop()
                return True, {"response": text_content.strip()}

        spinner.stop()

        if not function_calls:
            break

        async def execute_function(func_call):
            print_formatted_text(FormattedText([('class:bold', f"Executing function: {func_call['name']}")]), style=custom_style)

            if func_call["name"] == "set_api_config_dialog":
                func_call["arguments"]["spinner"] = spinner

            result = await execute_function_by_name(func_call["name"], **func_call["arguments"])
            return {"id": func_call["id"], "result": result}

        function_results = await asyncio.gather(*[execute_function(func_call) for func_call in function_calls])

        # Update messages with function calls and results
        new_message_content = []
        if text_content.strip():
            new_message_content.append({
                "type": "text",
                "text": text_content.strip()
            })

        for func_call in function_calls:
            func_call["arguments"].pop("spinner", None)

            if api_to_use == "openai":
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": func_call["name"],
                        "arguments": json.dumps(func_call["arguments"])
                    }
                })
            else:  # Anthropic
                new_message_content.append({
                    "type": "tool_use",
                    "id": func_call["id"],
                    "name": func_call["name"],
                    "input": func_call["arguments"]
                })

        if api_to_use == "anthropic" and new_message_content:
            messages.append({
                "role": "assistant",
                "content": new_message_content
            })

        for func_call, result in zip(function_calls, function_results):
            if api_to_use == "openai":
                messages.append({
                    "role": "function",
                    "name": func_call["name"],
                    "content": result["result"]
                })
            else:  # Anthropic
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": func_call["id"],
                            "content": result["result"]
                        }
                    ]
                })

        function_call_count += len(function_calls)

    # Formulate final response using the tool results
    if api_to_use == "openai":
        final_response = await openai_chat_completion_request(messages=messages, config=config, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from OpenAI"}
        final_message = final_response.choices[0].message.content
        return True, {"response": final_message}
    else:  # Anthropic
        final_response = await anthropic_chat_completion_request(messages=messages, config=config, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from Anthropic"}
        
        final_text_content = ""
        for content_item in final_response.content:
            if isinstance(content_item, TextBlock):
                final_text_content += content_item.text
        
        if not final_text_content:
            return False, {"error": "No text content in Anthropic final response"}
        
        return True, {"response": final_text_content.strip()}
