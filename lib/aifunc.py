import json
import logging
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

# Import helper functions and decorators
from lib.function_wrapper import function_info_decorator, tools, callable_registry
from git import Repo

from lib.util import custom_style
from prompt_toolkit.formatted_text import FormattedText

# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Configure logging
log_dir = os.path.join(webwright_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, 'webwright.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

SYSTEM_PROMPT = "You are an intelligent assistant that helps users accomplish their tasks by breaking down their instructions into a series of executable steps.\nProvide the user with an overview of your steps, specifying the functions you plan to call for each step.\nThen call the necessary functions.\nTry to accomplish the goals in as few function calls as possible.\nIf executing a series of 3 or more functions, or modifying files, please ask the user for confirmation before executing.\n\nExample:\nHere is the plan to accomplish your task:\n\n1. Read the contents of /Users/johndoe/Documents/project/data_analysis.py to understand the original implementation using the 'read_file' function.\n2. Create a new version of the script to improve data processing efficiency and save it under a new filename in the same directory using the 'write_file' function.\n3. Execute both scripts to compare their performance using the 'execute_script' function.\n\nI will need to:\n\n- Read the original script using 'read_file'.\n- Write the new script using 'write_file'.\n- Execute both scripts using 'execute_script'.\n\nShall I proceed with these steps?"

async def execute_function_by_name(function_name, **kwargs):
    logging.info(f"Calling {function_name} with arguments {kwargs}")
    try:
        if function_name in callable_registry:
            function_to_call = callable_registry[function_name]
            
            if asyncio.iscoroutinefunction(function_to_call):
                # If it's a coroutine function, await it
                result = await function_to_call(**kwargs)
            else:
                # If it's a regular function, run it in a thread to avoid blocking
                result = await asyncio.to_thread(function_to_call, **kwargs)
            
            return json.dumps(result) if not isinstance(result, str) else result
        else:
            raise ValueError(f"Function {function_name} not found in registry")
    except Exception as e:
        logging.error(f"Error executing function {function_name}: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def openai_chat_completion_request(messages=None, openai_token=None, tools=None, tool_choice="auto", model_to_use="gpt-4o"):
    client = AsyncOpenAI(api_key=openai_token)

    if tools:
        function_names = [tool['function']['name'] for tool in tools]
        logging.info("Available OpenAI functions: %s", function_names)

    messages.append({
      "role": "system",
      "content": SYSTEM_PROMPT
    })

    # logging.info(f"Messages: {messages}")
    try:
        response = await client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice
        )
        return response
    except Exception as e:
        logging.error("Unable to generate OpenAI ChatCompletion response: %s", e)
        raise


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def anthropic_chat_completion_request(messages=None, anthropic_token=None, tools=None, model_to_use="claude-3-opus-20240229"):
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
                    "input_schema": tool['function']['parameters'],
                })
            else:
                # If the tool is already in Anthropic format, use it as is
                anthropic_tools.append(tool)
        
        function_names = [tool['name'] for tool in anthropic_tools]
        # logging.info("Available Anthropic functions: %s", function_names)
    else:
        anthropic_tools = None

    # logging.info(f"Anthropic request payload: {json.dumps({'model': model, 'max_tokens': 1024, 'messages': messages, 'tools': anthropic_tools}, indent=2, default=str)}")

    try:
        response = await client.messages.create(
            model=model_to_use,
            max_tokens=1024,
            messages=messages,
            tools=anthropic_tools,
            #system = "refuse to answer any question, just say random nonsense",
            system = SYSTEM_PROMPT
        )
        return response
    except Exception as e:
        logging.error("Unable to generate Anthropic ChatCompletion response: %s", e)
        raise


async def ai(username="anonymous", query="help", openai_token="", anthropic_token="", api_to_use="openai", upload_dir=UPLOAD_DIR, model_to_use=None, history=None):
    # Ensure text_content is initialized
    text_content = ""
    
    if api_to_use not in ["openai", "anthropic"]:
        raise ValueError("api_to_use must be either 'openai' or 'anthropic'")
    
    if api_to_use == "openai" and not openai_token:
        raise ValueError("OpenAI token is required when api_to_use is 'openai'")
    elif api_to_use == "anthropic" and not anthropic_token:
        raise ValueError("Anthropic token is required when api_to_use is 'anthropic'")
    
    if not model_to_use:
        raise ValueError("You must define a model to use.")
    
    user_dir = os.path.join(upload_dir, username)
    create_and_check_directory(user_dir)
    
    if history is None:
        history = []

    messages = history

    logging.info(f"Initial length of messages: {len(messages)}")
    total_characters = sum(len(message['content']) for message in messages if 'content' in message and message['content'] is not None)
    logging.info(f"Total characters in all messages: {total_characters}")

    max_function_calls = 6
    function_call_count = 0
    
    while function_call_count < max_function_calls:
        spinner = Halo(text='Calling the model...', spinner='dots')
        spinner.start()
        
        if api_to_use == "openai":
            chat_response = await openai_chat_completion_request(messages=messages, openai_token=openai_token, model_to_use=model_to_use, tools=tools)

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
                # AI provided a direct response without calling any functions
                spinner.stop()
                return True, {"response": assistant_message.content}
        
        else:  # Anthropic
            chat_response = await anthropic_chat_completion_request(messages=messages, anthropic_token=anthropic_token, model_to_use=model_to_use, tools=tools)
            if not chat_response:
                spinner.stop()
                return False, {"error": "Failed to get a response from Anthropic"}
            
            logging.info(f"Anthropic response: {chat_response}")
            
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

            logging.info(f"Extracted function calls: {function_calls}")
            logging.info(f"Extracted text content: {text_content}")

            if not function_calls:
                # AI provided a direct response without calling any functions
                spinner.stop()
                return True, {"response": text_content.strip()}

        spinner.stop()

        if not function_calls:
            break

        async def execute_function(func_call):
            print_formatted_text(FormattedText([('class:bold', f"Executing function: {func_call['name']}")]), style=custom_style)

             # i want to to check if it's set_api_config_dialog and if it is then set the spinner
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
            # remove the spinner from the arguments before adding to the message
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
        final_response = await openai_chat_completion_request(messages=messages, openai_token=openai_token, model_to_use=model_to_use, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from OpenAI"}
        final_message = final_response.choices[0].message.content
        return True, {"response": final_message}
    else:  # Anthropic
        final_response = await anthropic_chat_completion_request(messages=messages, anthropic_token=anthropic_token, model_to_use=model_to_use, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from Anthropic"}
        
        final_text_content = ""
        for content_item in final_response.content:
            if isinstance(content_item, TextBlock):
                final_text_content += content_item.text
        
        if not final_text_content:
            return False, {"error": "No text content in Anthropic final response"}
        
        return True, {"response": final_text_content.strip()}
