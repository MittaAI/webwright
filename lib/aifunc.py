import sys
import os
import random
import string
import math
import json
import re
import openai
import asyncio
import logging

import shutil
import subprocess
import importlib

from lib.util import get_anthropic_api_key, create_and_check_directory

from halo import Halo

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
    try:
        if function_name in callable_registry:
            function_to_call = callable_registry[function_name]
            result = await function_to_call(**kwargs) if asyncio.iscoroutinefunction(function_to_call) else function_to_call(**kwargs)
            return json.dumps(result) if not isinstance(result, str) else result
        else:
            raise ValueError(f"Function {function_name} not found in registry")
    except Exception as e:
        return json.dumps({"error": str(e)})


# Process the results of a chat completion
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def process_results(results: dict, function_info: dict, openai_token: str) -> str:
    try:
        if "success" in results and results["success"]:
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps explain the results of executed commands.\n\nSome commands, like 'help', output a list of available commands, so you may need to explain what each command does.\n\nSometimes, the functions output code, like between python``` and ```. In that case, you should output the code, and anything else said. Keep your explanations very short and clear, focusing on what a user would expect to see when a command outputs something.\n\nAvoid going into technical details or explaining the underlying functions. Just provide a concise, user-friendly description.\n\nIf there is a clear, direct answer, put it on its own line for emphasis.\n\nIf a command runs a program or script, be sure to include the output.\n\nDo not refer to the commands as functions or show the actual function calls, as users interact with these commands through a chat interface."},
                {"role": "user", "content": f"\n\n{json.dumps(results, indent=2)}\n\n{json.dumps(function_info, indent=2)}\n\n"}
            ]

            chat_response = await chat_completion_request_async(messages=messages, openai_token=openai_token)
            assistant_response = chat_response.choices[0].message.content.strip()
            return assistant_response
        else:
            if "response" in results:
                return results.get('response')
            if "error" in results:
                error_message = results.get('error')
                reason = results.get('reason')
                return f"The function execution failed with the following error: {error_message} {reason}"
            else:
                return "The function execution failed with an unknown error."
    except Exception as e:
        raise Exception(f"Error processing results: {str(e)}") from e


# Request a chat completion
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def chat_completion_request_async(messages=None, openai_token=None, tools=None, tool_choice=None, model="gpt-4o"):
    """
    Make an asynchronous request to OpenAI's chat completion API.
    """
    client = openai.AsyncOpenAI(api_key=openai_token)

    logging.info("tools")
    logging.info(tools)

    try:
        return await client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice=tool_choice)
    except Exception as e:
        logging.info("Unable to generate ChatCompletion response:", e)
        return None


async def ai(username="anonymous", query="help", openai_token="", anthropic_token="", upload_dir=UPLOAD_DIR, history=None):
    """
    Process a given query with OpenAI and execute a function based on the response.
    """
    if not openai_token:
        raise ValueError("OpenAI token is required")
    
    # log the history
    logging.info("HISTORY")
    logging.info(history)
    
    # Ensure the upload directory and the username directory under that exist
    user_dir = os.path.join(upload_dir, username)
    create_and_check_directory(user_dir)
    
    messages = [
        {"role": "system", "content": "You are an AI bot that picks functions to call based on the command query. Don't make assumptions, stay focused, set attention for well-formed responses. If there doesn't appear to be a function to call, you can simply answer the user using the chat function. If asked to write an expression for calculations, consider writing the expression in Python."}
    ]
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": query})
    
    logging.info("MESSAGES")
    logging.info(messages)

    # Get the function and parameters to call
    chat_response = await chat_completion_request_async(messages=messages, openai_token=openai_token, tools=tools)
    logging.info(chat_response)
    assistant_message = chat_response.choices[0].message
    
    if assistant_message.function_call is None and assistant_message.tool_calls is None:
        # No function call or tool calls, return the assistant's response
        return True, {"response": assistant_message.content}
        
    # Assume function_name and arguments are extracted from chat_response
    try:
        function_name = chat_response.choices[0].message.tool_calls[0].function.name
        arguments_json = chat_response.choices[0].message.tool_calls[0].function.arguments
        arguments = json.loads(arguments_json)
        
        spinner = Halo(text='Executing function...', spinner='dots')
        spinner.start()
        json_results_str = await execute_function_by_name(function_name, **arguments)
        logging.info(json_results_str)
        spinner.stop()
        
        results = json.loads(json_results_str) if not isinstance(json_results_str, dict) else json_results_str

        # Move 'arguments' into the 'results' dictionary
        results['arguments'] = arguments
        results['function_name'] = function_name
        return True, results
        
    except Exception as ex:
        logging.info("ERRRORORRRRR")
        logging.info(ex)
        # Return False and the error message
        return False, {'error': str(ex)}