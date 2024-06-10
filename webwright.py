import os
import sys
import pprint
import json
import time
import random
import traceback
from asyncio import get_event_loop, new_event_loop, set_event_loop
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
from lib.util import setup_ssh_key, get_openai_api_key, set_openai_api_key
from lib.util import get_username
from lib.aifunc import ai, process_results

# user
username = get_username()

# build history and session
history_file = os.path.join(webwright_dir, '.webwright_history')
history = FileHistory(history_file)

async def process_shell_query(username, query, openai_token):
    print("system> Calling GPTChat for command...please wait.")
    try:
        success, results = await ai(username=username, query=query, openai_token=openai_token)
        if success:
            function_info = results.get("arguments", {}).get("function_info", {})
            explanation = await process_results(results, function_info, openai_token)
            print(f"system> {explanation}")
        else:
            if "error" in results:
                error_message = results["error"]
                print(f"system> Error: {error_message}")
            else:
                print("system> An unknown error occurred.")
    except Exception as e:
        print(f"system> Error: {str(e)}")

async def main():
    openai_token = get_openai_api_key()
    if not openai_token:
        openai_token = input("Please enter your OpenAI API key: ")
        set_openai_api_key(openai_token)

    setup_ssh_key()

    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    while True:
        try:
            question = await session.prompt_async(f"{username}[shell]> ")
            # Check if the question is empty (user just hit enter)
            if question.strip() == "":
                print()  # Print a newline character for line feed
                continue
            
            if question.strip() == 'quit' or question.strip() == 'exit':
                print("system> Bye!")
                sys.exit()
            await process_shell_query(username, question, openai_token)
        except KeyboardInterrupt:
            print("system>", random.choice(["Bye!", "Later!", "Nice working with you."]))
            break
        except RuntimeError as e:
            if str(e) == 'Event loop is closed':
                pass  # Ignore the exception if the event loop is closed
            else:
                raise  # Re-raise the exception for other RuntimeError instances

if __name__ == "__main__":
    # Create a new event loop and set it as the default
    event_loop = new_event_loop()
    set_event_loop(event_loop)
    # Run the main coroutine using the event loop
    event_loop.run_until_complete(main())
    event_loop.close()