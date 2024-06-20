# aifunc.py

import json
import logging
import os
import asyncio
from tenacity import retry, wait_random_exponential, stop_after_attempt
from halo import Halo

# OpenAI imports
from openai import AsyncOpenAI

# Anthropic imports
from anthropic import AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT

# Utility imports (assuming these are from your local modules)
from lib.util import create_and_check_directory

# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Configure logging
log_dir = os.path.join(webwright_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, 'webwright.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import helper functions and decorators
from lib.function_wrapper import function_info_decorator, tools, callable_registry
from tenacity import retry, wait_random_exponential, stop_after_attempt

from git import Repo

# Storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

# Execute function by name
async def execute_function_by_name(function_name, **kwargs):
    logging.info(f"calling {function_name}")
    try:
        if function_name in callable_registry:
            function_to_call = callable_registry[function_name]
            result = await function_to_call(**kwargs) if asyncio.iscoroutinefunction(function_to_call) else function_to_call(**kwargs)
            return json.dumps(result) if not isinstance(result, str) else result
        else:
            raise ValueError(f"Function {function_name} not found in registry")
    except Exception as e:
        return json.dumps({"error": str(e)})


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def openai_chat_completion_request(messages=None, openai_token=None, tools=None, tool_choice=None, model="gpt-4o"):
    """
    Make an asynchronous request to OpenAI's chat completion API.
    """
    client = AsyncOpenAI(api_key=openai_token)

    if tools:
        function_names = [tool['function']['name'] for tool in tools]
        logging.info("Available OpenAI functions: %s", function_names)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )
        return response
    except Exception as e:
        logging.error("Unable to generate OpenAI ChatCompletion response: %s", e)
        raise

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def anthropic_chat_completion_request(messages=None, anthropic_token=None, tools=None, model="claude-3-opus-20240229"):
    """
    Make an asynchronous request to Anthropic's chat completion API.
    """
    client = AsyncAnthropic(api_key=anthropic_token)
    
    if tools:
        # Anthropic expects tools in a different format
        anthropic_tools = []
        for tool in tools:
            if 'function' in tool:
                anthropic_tools.append({
                    "name": tool['function']['name'],
                    "description": tool['function']['description'],
                    "input_schema": tool['function']['parameters']
                })
            else:
                # If the tool is already in Anthropic format, use it as is
                anthropic_tools.append(tool)
        
        function_names = [tool['name'] for tool in anthropic_tools]
        logging.info("Available Anthropic functions: %s", function_names)
    else:
        anthropic_tools = None

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            messages=messages,
            tools=anthropic_tools
        )
        return response
    except Exception as e:
        logging.error("Unable to generate Anthropic ChatCompletion response: %s", e)
        raise


async def ai(username="anonymous", query="help", openai_token="", anthropic_token="", function_call_model="openai", upload_dir=UPLOAD_DIR, history=None):
    """
    Process a given query with OpenAI or Anthropic and execute a function based on the response.
    """
    if function_call_model not in ["openai", "anthropic"]:
        raise ValueError("function_call_model must be either 'openai' or 'anthropic'")
    
    if function_call_model == "openai" and not openai_token:
        raise ValueError("OpenAI token is required when function_call_model is 'openai'")
    elif function_call_model == "anthropic" and not anthropic_token:
        raise ValueError("Anthropic token is required when function_call_model is 'anthropic'")
    
    # Ensure the upload directory and the username directory under that exist
    user_dir = os.path.join(upload_dir, username)
    create_and_check_directory(user_dir)
    
    if history is None:
        history = []

    messages = history + [{"role": "user", "content": query}]

    function_name = None
    arguments = None
    tool_use_id = None

    # Get the function and parameters to call
    if function_call_model == "openai":
        chat_response = await openai_chat_completion_request(messages=messages, openai_token=openai_token, tools=tools)
        if not chat_response:
            return False, {"error": "Failed to get a response from OpenAI"}
        assistant_message = chat_response.choices[0].message
        
        if assistant_message.tool_calls:
            function_call = assistant_message.tool_calls[0].function
            function_name = function_call.name
            arguments = json.loads(function_call.arguments)
            tool_use_id = assistant_message.tool_calls[0].id
        else:
            history.append({"role": "assistant", "content": assistant_message.content})
            return True, {"response": assistant_message.content, "history": history}
    else:  # Anthropic
        logging.info(f"calling anthropic with messages: {messages}")
        chat_response = await anthropic_chat_completion_request(messages=messages, anthropic_token=anthropic_token, tools=tools)
        if not chat_response:
            return False, {"error": "Failed to get a response from Anthropic"}
        
        assistant_message = chat_response.content
        tool_use = next((item for item in assistant_message if item.type == 'tool_use'), None)
        
        if tool_use:
            function_name = tool_use.name
            arguments = tool_use.input
            tool_use_id = tool_use.id
        else:
            text_content = next((item.text for item in assistant_message if item.type == 'text'), None)
            if text_content:
                history.append({"role": "assistant", "content": text_content})
                return True, {"response": text_content, "history": history}
            else:
                return False, {"error": "Unexpected response format from Anthropic"}

    if not function_name or not arguments:
        return True, {"response": "No function call was made.", "history": history}

    # Extract follow-up function if present
    follow_up_function = arguments.pop('follow_up_function', None)
    
    spinner = Halo(text='Executing function...', spinner='dots')
    spinner.start()
    json_results_str = await execute_function_by_name(function_name, **arguments)
    logging.info(json_results_str)
    spinner.stop()
    
    results = json.loads(json_results_str) if not isinstance(json_results_str, dict) else json_results_str

    # Move 'arguments' and 'follow_up_function' into the 'results' dictionary
    results['arguments'] = arguments
    results['function_name'] = function_name
    if follow_up_function:
        results['follow_up_function'] = follow_up_function

    # Formulate final response using the tool results
    if function_call_model == "openai":
        messages.append({
            "role": "assistant",
            "content": None,
            "function_call": {
                "name": function_name,
                "arguments": json.dumps(arguments)
            }
        })
        messages.append({
            "role": "function",
            "name": function_name,
            "content": json.dumps(results)
        })
        final_response = await openai_chat_completion_request(messages=messages, openai_token=openai_token, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from OpenAI"}
        final_message = final_response.choices[0].message.content
        history.append({"role": "assistant", "content": final_message})
        return True, {"response": final_message, "history": history}
    else:  # Anthropic
        messages.append({
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_use_id,
                    "name": function_name,
                    "input": arguments
                }
            ]
        })
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(results)
                }
            ]
        })
        final_response = await anthropic_chat_completion_request(messages=messages, anthropic_token=anthropic_token, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from Anthropic"}
        final_message = next(item.text for item in final_response.content if item.type == 'text')
        history.append({"role": "assistant", "content": final_message})
        return True, {"response": final_message, "history": history}