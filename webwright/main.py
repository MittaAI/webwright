import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import traceback
import asyncio
import datetime

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.clipboard import ClipboardData

from lib.config import Config
from lib.util import format_response, get_logger, custom_style


try:
    from lib.aifunc import ai
    from git import Repo
except ImportError as e:
    if 'git' in str(e):
        print_formatted_text(FormattedText([
            ('class:error', "\nsystem> Git executable not found.\n"),
            ('class:instruction', "\nPlease install Git using the following steps:\n"),
            ('class:instruction', "\n1. Install Conda from "),
            ('class:inline-code', "https://docs.conda.io/en/latest/miniconda.html"),
            ('class:instruction', "\n\n2. Create and activate a Conda environment:\n"),
            ('class:code', "   conda create -n webwright python=3.10\n"),
            ('class:code', "   conda activate webwright\n"),
            ('class:instruction', "\n3. Install Git in the Conda environment:\n"),
            ('class:code', "   conda install git\n"),
            ('class:instruction', "\n4. Restart webwright:\n"),
            ('class:code', "   webwright\n"),
        ]), style=custom_style)
        sys.exit(1)
    else:
        raise

# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Setup logging
logger = get_logger()

# Initialize Config
config = Config()

# User
username = config.get_username()

# Key bindings
bindings = KeyBindings()

@bindings.add('c-v')
def _(event):
    print("system> Use mouse right-click to paste.")
    clipboard_data = event.app.clipboard.get_data()
    if isinstance(clipboard_data, ClipboardData):
        event.current_buffer.insert_text(clipboard_data.text)

# Build history and session
history_file = os.path.join(webwright_dir, 'webwright_history')
history = FileHistory(history_file)
session = PromptSession(history=history, key_bindings=bindings)

def custom_exception_handler(loop, context):
    exception = context.get("exception")
    
    if exception:
        logger.error(f"Caught exception: {exception}")
    else:
        logger.error(f"Caught error: {context['message']}")

    print(f"Unhandled exception: {exception}")
    print("Press ENTER to continue...")

    if isinstance(exception, OSError) and exception.winerror == 10038:
        print("Handled WinError 10038")
    else:
        loop.default_exception_handler(context)

async def process_shell_query(username, query, config, conversation_history):
    try:
        success, results = await ai(username=username, query=query, config=config, history=conversation_history)
        
        logger.debug(f"AI response: {results}")

        if success:
            if "response" in results and results["response"] is not None:
                return True, {"explanation": results["response"]}
            elif "function_call" in results:
                try:
                    function_call = results["function_call"]
                    arguments = json.loads(function_call.arguments)
                    function_response = f"Function call: {function_call.name}\nArguments: {json.dumps(arguments, indent=2)}"
                    return True, {"explanation": function_response}
                except json.JSONDecodeError:
                    function_response = f"Function call: {function_call.name}\nArguments (raw): {function_call.arguments}"
                    return True, {"explanation": function_response}
            else:
                error_msg = "An unexpected response format was received."
                print(results)
                print_formatted_text(FormattedText([('class:error', f"system> Error: {error_msg}")]), style=custom_style)
                return False, {"error": error_msg}
        else:
            if "error" in results:
                error_message = results["error"]
                print_formatted_text(FormattedText([('class:error', f"system> Error: {error_message}")]), style=custom_style)
                logger.error(f"Error: {error_message}")
            else:
                error_message = "An unknown error occurred."
                print_formatted_text(FormattedText([('class:error', f"system> Error: {error_message}")]), style=custom_style)
            return False, {"error": error_message}
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print_formatted_text(FormattedText([('class:error', f"system> {error_message}")]), style=custom_style)
        logger.error(error_message)
        logger.error(traceback.format_exc())
        return False, {"error": error_message}

def log_conversation(username, message, role):
    webwright_dir = os.path.expanduser('~/.webwright')
    log_dir = os.path.join(webwright_dir, 'conversation_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{username}_conversation.log")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{role}: {message}\n")

async def main(config):
    conversation_history = []
    username = config.get_username()

    while True:
        try:
            # Reload the configuration at the start of each loop
            config.reload_config()

            current_path = os.getcwd().replace(os.path.expanduser('~'), '~')
            
            # Fetch the latest API and model information
            api_to_use = config.get_config_value("config", "PREFERRED_API")
            if api_to_use == "openai":
                model_to_use = config.get_config_value("config", "OPENAI_MODEL")
            elif api_to_use == "anthropic":
                model_to_use = config.get_config_value("config", "ANTHROPIC_MODEL")
            else:
                api_to_use = "unknown"
                model_to_use = "unknown"
            
            prompt_text = [
                ('class:username', f"{username}@"),
                ('class:model', f"{api_to_use}/{model_to_use} "),
                ('class:path', f"{current_path} $ ")
            ]

            question = await session.prompt_async(FormattedText(prompt_text), style=custom_style)

            if question.strip() == "":
                continue
            
            if question.strip().lower() in ['quit', 'exit']:
                print("system> Bye!")
                return
            
            conversation_history.append({"role": "user", "content": question})
            log_conversation(username, question, "user")

            success, results = await process_shell_query(username, question, config, conversation_history)
            
            if success and "explanation" in results:
                formatted_response = format_response(results['explanation'])
                print_formatted_text(formatted_response, style=custom_style)
                conversation_history.append({"role": "assistant", "content": results["explanation"]})
                log_conversation(username, results["explanation"], "assistant")
            elif not success and "error" in results:
                # Error messages are already handled in process_shell_query
                pass
            else:
                print_formatted_text(FormattedText([('class:error', "system> An unexpected error occurred.")]), style=custom_style)

        except Exception as e:
            print_formatted_text(FormattedText([('class:error', f"system> Error: {str(e)}")]), style=custom_style)
            logger.error(f"Error: {str(e)}")
            logger.error(traceback.format_exc())

def entry_point():
    config = Config()
    api_to_use, openai_token, anthropic_token, model_to_use = config.determine_api_to_use()

    if api_to_use is None:
        print("No API selected. Exiting program.")
        sys.exit(1)
    
    if not openai_token and not anthropic_token:
        print("Error: Neither OpenAI nor Anthropic API key is set.")
        print("Please set at least one API key in your environment variables or configuration file.")
        print("Use OPENAI_API_KEY for OpenAI or ANTHROPIC_API_KEY for Anthropic.")
        sys.exit(1)
    
    config.setup_ssh_key()

    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(custom_exception_handler)

    try:
        loop.run_until_complete(main(config))
    except KeyboardInterrupt:
        print("system> KeyboardInterrupt received, shutting down...")
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        print_formatted_text(FormattedText([('class:success', "system> Shutdown complete.")]), style=custom_style)

if __name__ == "__main__":
    entry_point()