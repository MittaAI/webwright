import os
import sys
import logging
import pprint
import json
import time
import random
import traceback
import asyncio
import openai
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
from lib.util import setup_ssh_key, get_openai_api_key, set_openai_api_key, get_anthropic_api_key, set_anthropic_api_key
from lib.util import get_username
from halo import Halo

try:
    from lib.aifunc import ai, process_results
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

# Build history and session
history_file = os.path.join(webwright_dir, '.webwright_history')
history = FileHistory(history_file)
session = PromptSession(history=history)

async def process_shell_query(username, query, openai_token, anthropic_token, thread_id):
    spinner = Halo(text='Calling GPTChat for command...please wait.', spinner='dots')
    spinner.start()
    try:
        success, results = await ai(username=username, query=query, openai_token=openai_token, anthropic_token=anthropic_token, thread_id=thread_id)
        spinner.stop()
        if success:
            function_info = results.get("arguments", {}).get("function_info", {})
            explanation = await process_results(results, function_info, openai_token)
            print(f"system> {explanation}")
        else:
            if "error" in results:
                error_message = results["error"]
                print(f"system> Error: {error_message}")
                logging.error(f"Error: {error_message}")
            else:
                print("system> An unknown error occurred.")
    except Exception as e:
        spinner.stop()
        error_message = f"system> Error: {str(e)}"
        print(error_message)
        logging.error(error_message)
        logging.error(traceback.format_exc())

async def main():
    openai_token = get_openai_api_key()
    if not openai_token:
        openai_token = input("Please enter your OpenAI API key: ")
        set_openai_api_key(openai_token)
        
    anthropic_token = get_anthropic_api_key()
    if not anthropic_token:
        anthropic_token = input("Please enter your Anthropic API key: ")
        set_anthropic_api_key(anthropic_token)

    setup_ssh_key()
    
    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Initialize the OpenAI client with the API key
    openai.api_key = openai_token

    # Create a new thread
    thread = openai.beta.threads.create()
    thread_id = thread.id
    
    while True:
        try:
            question = await session.prompt_async(f"{username}[shell]> ")
            # Check if the question is empty (user just hit enter)
            if question.strip() == "":
                print()  # Print a newline character for line feed
                continue
            
            if question.strip() == 'quit' or question.strip() == 'exit':
                print("system> Bye!")
                return
            
            await process_shell_query(username, question, openai_token, anthropic_token, thread_id)
        except KeyboardInterrupt:
            print("system>", random.choice(["Bye!", "Later!", "Nice working with you."]))
            break
        except RuntimeError as e:
            if str(e) == 'Event loop is closed':
                pass  # Ignore the exception if the event loop is closed
            else:
                raise  # Re-raise the exception for other RuntimeError instances
        except Exception as e:
            error_message = f"system> Error: {str(e)}"
            print(error_message)
            logging.error(error_message)
            logging.error(traceback.format_exc())

def entry_point():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("system> Exiting gracefully...")
        # Cancel all running tasks
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        for task in tasks:
            task.cancel()
        # Ensure the event loop is closed
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
    except Exception as e:
        print(f"system> Error during shutdown: {str(e)}")
        logging.error(f"Error during shutdown: {str(e)}")
        logging.error(traceback.format_exc())
    finally:
        print("system> Shutdown complete.")

if __name__ == "__main__":
    entry_point()