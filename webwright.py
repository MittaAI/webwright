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

from lib.util import get_username
from lib.aifunc import ai

# user
username = get_username()

# build history and session
history = FileHistory(".webwright_history")
session = PromptSession(history=history)


async def process_shell_query(username, query, openai_token):
    print("system> Calling GPTChat for command...please wait.")
    try:
        success, results = await ai(username=username, query=query, openai_token=openai_token)
        if success:
            if "response" in results:
                response_content = results["response"]
                print(f"system> {response_content}")
            else:
                function_result = results
                print(f"system> Result: {function_result}")
        else:
            if "error" in results:
                error_message = results["error"]
                print(f"system> Error: {error_message}")
            else:
                failure_reason = results.get("reason", "Unknown failure reason")
                print(f"system> Operation failed: {failure_reason}")
    except Exception as e:
        print(f"system> Error: {e}")


async def main():
    openai_token = os.environ.get("OPENAI_API_KEY")
    if not openai_token:
        print("system> Error: OPENAI_API_KEY environment variable not set.")
        return

    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')  # <-- Add this line
    
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