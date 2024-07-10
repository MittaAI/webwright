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
from git import Repo

# Storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

SYSTEM_PROMPT = "You are an intelligent assistant that helps users accomplish their tasks by breaking down their instructions into a series of executable steps. Provide the user with an overview of your steps, then call the necessary functions. If executing a series of 3 or more functions, or modifying files please ask the user for confirmation before executing."

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

    logging.info(f"Messages: {messages}")
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

    messages = history

    messages.append({
        "role": "system",
        "content": SYSTEM_PROMPT
    })

    max_function_calls = 6
    function_call_count = 0
    
    while function_call_count < max_function_calls:

        # Get the initial response
        spinner = Halo(text='Calling the model...', spinner='dots')
        spinner.start()
        
        if function_call_model == "openai":
            chat_response = await openai_chat_completion_request(messages=messages, openai_token=openai_token, tools=tools)

            if not chat_response:
                spinner.stop()
                return False, {"error": "Failed to get a response from OpenAI"}
            assistant_message = chat_response.choices[0].message
            
            if assistant_message.tool_calls:
                function_call = assistant_message.tool_calls[0].function
                function_name = function_call.name
                arguments = json.loads(function_call.arguments)
                tool_use_id = assistant_message.tool_calls[0].id
            else:
                spinner.stop()
                return True, {"response": assistant_message.content}
        else:  # Anthropic
            chat_response = await anthropic_chat_completion_request(messages=messages, anthropic_token=anthropic_token, tools=tools)
            if not chat_response:
                spinner.stop()
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
                    spinner.stop()
                    return True, {"response": text_content}
                else:
                    spinner.stop()
                    return False, {"error": "Unexpected response format from Anthropic"}

        spinner.stop()

        if not function_name:
            break

        # Execute the function
        spinner = Halo(text='Executing function...', spinner='dots')
        spinner.start()
        json_results_str = await execute_function_by_name(function_name, **arguments)
        logging.info(json_results_str)
        spinner.stop()
    
        results = json.loads(json_results_str) if not isinstance(json_results_str, dict) else json_results_str
        
        # Update messages with the function call and its result
        if function_call_model == "openai":
            messages += [
                {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": json.dumps(arguments)
                    }
                },
                {
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(results)
                }
            ]
        else:  # Anthropic
            messages += [
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": tool_use_id,
                            "name": function_name,
                            "input": arguments
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(results)
                        }
                    ]
                }
            ]

        function_call_count += 1

    # Formulate final response using the tool results
    if function_call_model == "openai":
        final_response = await openai_chat_completion_request(messages=messages, openai_token=openai_token, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from OpenAI"}
        final_message = final_response.choices[0].message.content
        return True, {"response": final_message}
    else:  # Anthropic
        final_response = await anthropic_chat_completion_request(messages=messages, anthropic_token=anthropic_token, tools=tools)
        if not final_response:
            return False, {"error": "Failed to get a final response from Anthropic"}
        
        text_content = next((item.text for item in final_response.content if item.type == 'text'), None)
        if text_content is None:
            return False, {"error": "No text content in Anthropic response"}
        
        return True, {"response": text_content}
