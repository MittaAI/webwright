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

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage

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


def ollama_chat_completion_request(messages, config, tools):
    llm = ChatOllama(
        model = 'llama3-groq-tool-use',
        temperature=0
    ).bind_tools(tools)
    return llm.invoke(messages)

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
        
        chat_response = ollama_chat_completion_request(messages=messages, config=config, tools=tools)
        assistant_message = chat_response

        if assistant_message.tool_calls:
            function_calls = []
            for tool_call in assistant_message.tool_calls:
                """
                try:
                  function_calls.append({
                    "name": tool_call["function.name"],
                    "arguments": tool_call["args"],
                    "id": tool_call.id
                  })
                except Exception as e:
                  print(f"Failed to process tool call: {tool_call}")
                  print(f"Error: {e}")
                """
                function_calls.append({
                  "name": tool_call["name"],
                  "arguments": tool_call["args"],
                  "id": tool_call["id"]
                })
        else:
            break

        async def execute_function(func_call):
            print_formatted_text(FormattedText([('class:bold', f"Executing function: {func_call['name']}")]), style=custom_style)

            if func_call["name"] == "set_api_config_dialog":
                func_call["arguments"]["spinner"] = spinner

            result = await execute_function_by_name(func_call["name"], **func_call["arguments"])
            return {"id": func_call["id"], "result": result}

        for func_call in function_calls:
            result = await execute_function(func_call)
            messages.append(ToolMessage(result["result"], tool_call_id=result["id"]))

    final_response = ollama_chat_completion_request(messages=messages, config=config, tools=tools)
    return True, final_response


if __name__ == "__main__":
    ai(username="anonymous", query="ell me the contents of /Users/andylegrand/Desktop/litellm_test/test using cat file", config=None, upload_dir=UPLOAD_DIR, history=None)
    print("Done")