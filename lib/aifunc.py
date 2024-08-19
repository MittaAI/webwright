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

import ollama

# This a modified 


# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Configure logging
logger = get_logger()

# Storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

SYSTEM_PROMPT = """
You are a helpful assistant with tool calling capabilities. Respond in this format:
{
  "message": "Your response here",
  "tool_calls": [{"name": function name, "arguments": dictionary of function arguments}]
}
If you recieve a request which does not require a tool call, respond normally and leave the functions field empty, otherwise use the message field to explain the tool call (eg. To view the contents of text.txt I will call the cat_file function). If multiple tools are used, put tools call in array format. If you recieve a request to do something you cannot normally do (ie view or modify a file) look for a function you can use to accomplish it.

You have access to the following functions:
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

async def ollama_chat_completion_request(messages=None, config=None, tools=None):
    prompt_with_tools = SYSTEM_PROMPT + str(tools)
    new_messages = messages.copy()
    new_messages.insert(0, {'role': 'system', 'content': prompt_with_tools})

    res = ollama.chat(
        model='llama3.1',
        messages=new_messages,
    )

    # convert to json format
    res = json.loads(res['message']['content'])

    return res


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
        
        chat_response = await ollama_chat_completion_request(messages=messages, config=config, tools=tools)
        assistant_message = chat_response

        print(f"Assistant message: {assistant_message}")

        if assistant_message["tool_calls"]:
          function_calls = []
          for tool_call in assistant_message["tool_calls"]:
              try:
                function_calls.append({
                  "name": tool_call["name"],
                  "arguments": tool_call["arguments"],
                })
              except Exception as e:
                print(f"Failed to process tool call: {tool_call}")
                print(f"Error: {e}")

        spinner.stop()

        if not function_calls:
            break

        async def execute_function(func_call):
            print_formatted_text(FormattedText([('class:bold', f"Executing function: {func_call['name']}")]), style=custom_style)

            if func_call["name"] == "set_api_config_dialog":
                func_call["arguments"]["spinner"] = spinner

            result = await execute_function_by_name(func_call["name"], **func_call["arguments"])
            return {"name": func_call["name"], "result": result}

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
