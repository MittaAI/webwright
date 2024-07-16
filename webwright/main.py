# Test header
# This is a test modification of the main.py file

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

import traceback
import asyncio

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import FormattedText, PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition
from prompt_toolkit.clipboard import ClipboardData
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog

from lib.util import setup_ssh_key, get_openai_api_key, set_openai_api_key, get_anthropic_api_key, set_anthropic_api_key
from lib.util import get_username
from lib.util import format_response
from lib.util import determine_api_to_use
from lib.util import setup_logging, get_logger

from halo import Halo

from custom_style import custom_style

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

# User
username = get_username()

# Key bindings
bindings = KeyBindings()

# Intercept Ctrl+V
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
    # Extract the exception
    exception = context.get("exception")
    
    if exception:
        logger.error(f"Caught exception: {exception}")
    else:
        logger.error(f"Caught error: {context['message']}")

    # Log the exception and prevent the program from crashing
    print(f"Unhandled exception: {exception}")
    print("Press ENTER to continue...")

    # Optionally: Handle specific exceptions
    if isinstance(exception, OSError) and exception.winerror == 10038:
        print("Handled WinError 10038")
    else:
        loop.default_exception_handler(context)

async def process_shell_query(username, query, openai_token, anthropic_token, conversation_history, api_to_use):
    try:
        success, results = await ai(username=username, query=query, openai_token=openai_token, anthropic_token=anthropic_token, api_to_use=api_to_use, history=conversation_history)
        
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


async def main(openai_token, anthropic_token, api_to_use="openai"):
    conversation_history = []  # Initialize conversation history

    while True:
        # logger.info(f"Conversation history: {conversation_history}")
        try:
            current_path = os.getcwd().replace(os.path.expanduser('~'), '~')
            
            prompt_text = [
                ('class:username', f"{username}@"),
                ('class:model', f"{api_to_use} "),
                ('class:path', f"{current_path} $ ")
            ]

            question = await session.prompt_async(FormattedText(prompt_text), style=custom_style)

            # Check if the question is empty (user just hit enter)
            if question.strip() == "":
                continue
            
            if question.strip().lower() in ['quit', 'exit']:
                print("system> Bye!")
                sys.exit()
            
            conversation_history.append({"role": "user", "content": question})
            # logger.info(f"Main: Added user message to history. Current history: {conversation_history}")
            
            success, results = await process_shell_query(username, question, openai_token, anthropic_token, conversation_history, api_to_use)
            
            if success and "explanation" in results:
                formatted_response = format_response(results['explanation'])
                print_formatted_text(formatted_response, style=custom_style)
                conversation_history.append({"role": "assistant", "content": results["explanation"]})
                # logger.info(f"Main: Added assistant response to history. Current history: {conversation_history}")
            elif not success and "error" in results:
                # Error messages are now handled in process_shell_query, so we don't need to print them here
                pass
            else:
                print_formatted_text(FormattedText([('class:error', "system> An unexpected error occurred.")]), style=custom_style)

        except Exception as e:
            print_formatted_text(FormattedText([('class:error', f"system> Error: {str(e)}")]), style=custom_style)
            logger.error(f"Error: {str(e)}")
            logger.error(traceback.format_exc())


def entry_point():
    # Get configs
    api_to_use, openai_token, anthropic_token, function_call_model = determine_api_to_use()

    if api_to_use is None:
        print("No API selected. Exiting program.")
        sys.exit(1)
    
    if not openai_token and not anthropic_token:
        print("Error: Neither OpenAI nor Anthropic API key is set.")
        print("Please set at least one API key in your environment variables or configuration file.")
        print("Use OPENAI_API_KEY for OpenAI or ANTHROPIC_API_KEY for Anthropic.")
        sys.exit(1)
    
    setup_ssh_key()

    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')

    # setup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set the custom exception handler
    loop.set_exception_handler(custom_exception_handler)

    try:
        loop.run_until_complete(main(openai_token=openai_token, anthropic_token=anthropic_token, api_to_use=api_to_use))

    except KeyboardInterrupt:
        print("system> KeyboardInterrupt received, cancelling tasks...")
        tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        for task in tasks:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        loop.run_until_complete(loop.shutdown_asyncgens())
    except OSError as e:
        if e.winerror == 10038:
            print_formatted_text(FormattedText([('class:error', f"system> Handled WinError 10038: {str(e)}")]), style=custom_style)
            logger.error(f"Handled WinError 10038: {str(e)}")
        else:
            raise
    except Exception as e:
        print(f"system> Error during shutdown: {str(e)}")
        logger.error(f"Error during shutdown: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        print("system> Closing event loop.")
        loop.close()
        print_formatted_text(FormattedText([('class:success', "system> Shutdown complete.")]), style=custom_style)


if __name__ == "__main__":
    entry_point()
