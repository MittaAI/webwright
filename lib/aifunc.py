import json
import os
import asyncio
from tenacity import retry, wait_random_exponential, stop_after_attempt
from halo import Halo
from datetime import datetime

# Utility imports (assuming these are from your local modules)
from lib.util import create_and_check_directory
from prompt_toolkit import PromptSession, print_formatted_text
from lib.util import get_logger
from lib.util import setup_function_logging

# Import helper functions and decorators
from lib.function_wrapper import function_info_decorator, tools, callable_registry
from git import Repo

from lib.util import custom_style
from lib.util import format_response
from prompt_toolkit.formatted_text import FormattedText

from lib.llm import llm_wrapper
from lib.omnilog import OmniLogVectorStore

import traceback
import inspect

# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Configure logging
logger = get_logger()

# Storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

async def execute_function_by_name(function_name, f_config, olog_history, **kwargs):
    logger.info(f"Calling {function_name} with arguments {kwargs}")
    
    if function_name not in callable_registry:
        logger.error(f"Function {function_name} not found in registry")
        return json.dumps({"error": f"Function {function_name} not found in registry"})
    
    try:
        func_logger = setup_function_logging(function_name)
        func_logger.info(f"Function {function_name} called with arguments: {kwargs}")
        function_to_call = callable_registry[function_name]
        
        # Check if the function accepts 'olog' as a parameter
        function_params = inspect.signature(function_to_call).parameters
        if 'olog' in function_params:
            kwargs['olog'] = olog_history

        if 'config' in function_params:
            kwargs['config'] = f_config

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

async def ai(username="anonymous", config=None, upload_dir=UPLOAD_DIR, olog: OmniLogVectorStore = None):
    max_function_calls = 6
    function_call_count = 0
    
    # get the LLM wrapper
    llm = llm_wrapper(config=config)

    # loop over max_function_calls
    while function_call_count < max_function_calls:
        messages = olog.get_recent_entries(10)
        spinner = Halo(text='Thinking...')
        spinner.start()
        
        try:
            llm_response = await llm.call_llm_api(messages=messages, tools=tools, tool_choice="auto")
        except Exception as e:
            raise Exception(f"Failed to get a response from LLM: {str(e)}")
        
        if not llm_response:
            raise Exception("Empty response from LLM")
        
        spinner.stop()
        spinner.clear()
        
        if not llm_response.get("function_calls"):
            olog.add_entry({
                'content': llm_response["content"],
                'type': 'llm_response',
                'timestamp': datetime.now().isoformat()
            })
            return True

        for func_call in llm_response["function_calls"]:
            try:
                print_formatted_text(FormattedText([('class:bold', f"Executing function: {func_call['name']}")]), style=custom_style)
                
                if func_call["name"] == "set_api_config_dialog":
                    func_call["parameters"]["spinner"] = spinner
                
                result = await execute_function_by_name(func_call["name"], config, olog, **func_call["parameters"])
                
                # add llm response
                olog.add_entry({
                    'content': {
                        "tool": func_call["name"],
                        "parameters": json.dumps(func_call["parameters"]),
                        "response": result
                    },
                    'type': 'tool_call',
                    'timestamp': datetime.now().isoformat()
                })
                function_call_count += 1

            except json.JSONDecodeError as e:
                print(f"Failed to parse function arguments for {func_call.function.name}: {str(e)}")
            except Exception as e:
                print(traceback.format_exc())
                print(f"Error executing function")

    # function calls maxed out, do something
    return True
