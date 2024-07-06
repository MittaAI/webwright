import os
import sys
import logging
import pprint
import json
import time
import random
import traceback
import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import FormattedText, PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition
from prompt_toolkit.clipboard import ClipboardData

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

async def process_shell_query(username, query, openai_token, anthropic_token, conversation_history, function_call_model):
    try:
        success, results = await ai(username=username, query=query, openai_token=openai_token, anthropic_token=anthropic_token, function_call_model=function_call_model, history=conversation_history)
        
        logging.debug(f"AI response: {results}")
           
        if success:
            if "response" in results:
                return True, {"explanation": results["response"]}
            else:
                print("system> An unexpected response format was received.")
                return False, {"error": "Unexpected response format"}
        else:
            if "error" in results:
                error_message = results["error"]
                print(f"system> Error: {error_message}")
                logging.error(f"Error: {error_message}")
            else:
                print("system> An unknown error occurred.")
            return False, {"error": error_message if "error" in results else "Unknown error"}
    except Exception as e:
        error_message = f"system> Error: {str(e)}"
        print(error_message)
        logging.error(error_message)
        logging.error(traceback.format_exc())
        return False, {"error": error_message}

def format_response(response):
    formatted_text = FormattedText()
    lines = response.split('\n')
    in_code_block = False
    in_thinking_block = False
    code_lines = []

    for line in lines:
        if in_thinking_block:
            if '</thinking>' in line:
                in_thinking_block = False
                formatted_text.append(('', '\n'))  # Add a newline after thinking block
            continue
        
        if '<thinking>' in line:
            in_thinking_block = True
            formatted_text.append(('italic', 'thinking\n'))
            continue

        if line.startswith('```python'):
            in_code_block = True
            continue
        elif line.startswith('```') and in_code_block:
            in_code_block = False
            try:
                tokens = PygmentsTokens(PythonLexer().get_tokens(''.join(code_lines)))
                formatted_text.extend([(token[0], token[1]) for token in tokens])
            except Exception as e:
                # If tokenization fails, fall back to plain text
                formatted_text.extend([('', line + '\n') for line in code_lines])
            formatted_text.append(('', '\n'))
            code_lines = []
        elif in_code_block:
            code_lines.append(line + '\n')
        else:
            if line.startswith('**'):
                formatted_text.append(('bold', line[2:-2]))
                formatted_text.append(('', '\n'))
            else:
                formatted_text.append(('', line + '\n'))

    return formatted_text


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
            
            if question.strip() == 'quit' or question.strip() == 'exit':
                print("system> Bye!")
                sys.exit()
            
            conversation_history.append({"role": "user", "content": question})
            logging.info(f"Main: Added user message to history. Current history: {conversation_history}")
            
            success, results = await process_shell_query(username, question, openai_token, anthropic_token, conversation_history, function_call_model)
            
            if success and "explanation" in results:
                formatted_response = format_response(results['explanation'])
                print_formatted_text(formatted_response)
                conversation_history.append({"role": "assistant", "content": results["explanation"]})
                logging.info(f"Main: Added assistant response to history. Current history: {conversation_history}")
            else:
                print("system> An error occurred: " + results.get("error", "Unknown error"))

        except Exception as e:
            print(f"system> Error: {str(e)}")
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
