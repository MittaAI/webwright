import os
import sys
import logging
import pprint
import json
import time
import random
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

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

from lib.util import setup_ssh_key, get_openai_api_key, set_openai_api_key, get_anthropic_api_key, set_anthropic_api_key
from lib.util import get_username
from halo import Halo

try:
    from lib.aifunc import ai
    from git import Repo
except ImportError as e:
    if 'git' in str(e):
        print("system> Git executable not found.")
        print("system> Please install Git using the following steps:")
        print("1. Install Conda from https://docs.conda.io/en/latest/miniconda.html")
        print("2. Create and activate a Conda environment:")
        print("   conda create -n myenv python=3.10")
        print("   conda activate myenv")
        print("3. Install Git in the Conda environment:")
        print("   conda install git")
        print("4. Restart webwright:")
        print("   webwright")
        sys.exit(1)
    else:
        raise

# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Setup logging
log_dir = os.path.join(webwright_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, 'webwright.log'), level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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
history_file = os.path.join(webwright_dir, '.webwright_history')
history = FileHistory(history_file)
session = PromptSession(history=history, key_bindings=bindings)

custom_style = Style.from_dict({
    'code': '#ansiyellow',
    'header': '#ansigreen bold',
    'bold': 'bold',
    'inline-code': '#ansicyan',
    'error': '#ff8c00',  # Add this line for orange error messages
})

async def process_shell_query(username, query, openai_token, anthropic_token, conversation_history, function_call_model):
    try:
        success, results = await ai(username=username, query=query, openai_token=openai_token, anthropic_token=anthropic_token, function_call_model=function_call_model, history=conversation_history)
        
        logging.debug(f"AI response: {results}")

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
                logging.error(f"Error: {error_message}")
            else:
                error_message = "An unknown error occurred."
                print_formatted_text(FormattedText([('class:error', f"system> Error: {error_message}")]), style=custom_style)
            return False, {"error": error_message}
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print_formatted_text(FormattedText([('class:error', f"system> {error_message}")]), style=custom_style)
        logging.error(error_message)
        logging.error(traceback.format_exc())
        return False, {"error": error_message}

def format_response(response):
    if response is None:
        return FormattedText([('class:error', "No response to format.\n")])
    
    formatted_text = []
    lines = response.split('\n')
    in_code_block = False
    code_lines = []

    for line in lines:
        if line.startswith('```'):
            if in_code_block:
                # End of code block
                in_code_block = False
                formatted_text.append(('class:code', ''.join(code_lines)))
                code_lines = []
            else:
                # Start of code block
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line + '\n')
        else:
            # Handle headers
            if line.startswith('#'):
                level = len(line.split()[0])
                formatted_text.append(('class:header', line[level:].strip() + '\n'))
            # Handle bold text
            elif '**' in line:
                parts = line.split('**')
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        formatted_text.append(('', part))
                    else:
                        formatted_text.append(('class:bold', part))
                formatted_text.append(('', '\n'))
            # Handle inline code
            elif '`' in line:
                parts = line.split('`')
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        formatted_text.append(('', part))
                    else:
                        formatted_text.append(('class:inline-code', part))
                formatted_text.append(('', '\n'))
            else:
                formatted_text.append(('', line + '\n'))

    return FormattedText(formatted_text)

async def main():
    openai_token = get_openai_api_key()
    if not openai_token:
        openai_token = input("Please enter your OpenAI API key: ")
        set_openai_api_key(openai_token)
        
    anthropic_token = get_anthropic_api_key()
    if not anthropic_token:
        anthropic_token = input("Please enter your Anthropic API key: ")
        set_anthropic_api_key(anthropic_token)

    
    function_call_model = "openai"

    if not function_call_model:
        function_call_model = input("Choose function call model (openai/anthropic): ").lower()

        while function_call_model not in ["openai", "anthropic"]:
            function_call_model = input("Invalid choice. Please enter 'openai' or 'anthropic': ").lower()

    setup_ssh_key()
    
    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    conversation_history = []  # Initialize conversation history
    
    while True:
        logging.info(f"Conversation history: {conversation_history}")
        try:
            question = await session.prompt_async(f"{username}[{function_call_model}]> ")
            # Check if the question is empty (user just hit enter)
            if question.strip() == "":
                continue
            
            if question.strip().lower() in ['quit', 'exit']:
                print("system> Bye!")
                sys.exit()
            
            conversation_history.append({"role": "user", "content": question})
            logging.info(f"Main: Added user message to history. Current history: {conversation_history}")
            
            success, results = await process_shell_query(username, question, openai_token, anthropic_token, conversation_history, function_call_model)
            
            if success and "explanation" in results:
                formatted_response = format_response(results['explanation'])
                print_formatted_text(formatted_response, style=custom_style)
                conversation_history.append({"role": "assistant", "content": results["explanation"]})
                logging.info(f"Main: Added assistant response to history. Current history: {conversation_history}")
            elif not success and "error" in results:
                # Error messages are now handled in process_shell_query, so we don't need to print them here
                pass
            else:
                print_formatted_text(FormattedText([('class:error', "system> An unexpected error occurred.")]), style=custom_style)

        except Exception as e:
            print_formatted_text(FormattedText([('class:error', f"system> Error: {str(e)}")]), style=custom_style)
            logging.error(f"Error: {str(e)}")
            logging.error(traceback.format_exc())

def entry_point():
    try:
        print("starting")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("system> Exiting gracefully...")
        # Cancel all running tasks
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        for task in tasks:
            task.cancel()
        # Ensure the event loop is closed
        loop = asyncio.get_event_loop()
        if not loop is None and not loop.is_closed():
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
    except Exception as e:
        print(f"system> Error during shutdown: {str(e)}")
        logging.error(f"Error during shutdown: {str(e)}")
        logging.error(traceback.format_exc())
    finally:
        print("system> Shutdown complete.")

if __name__ == "__main__":
    print("main entry")
    entry_point()