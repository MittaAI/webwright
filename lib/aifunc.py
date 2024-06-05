import sys
import os
import random
import string
import math
import json

import openai
import asyncio
import logging

import shutil
import subprocess

# Configure logging
logging.basicConfig(filename='webwright.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import helper functions and decorators
from lib.function_wrapper import function_info_decorator, tools, callable_registry
from tenacity import retry, wait_random_exponential, stop_after_attempt

from git import Repo

# storage
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'screenshots')

# ensure directory exists
def create_and_check_directory(directory_path):
    try:
        # Attempt to create the directory (and any necessary parent directories)
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Directory '{directory_path}' ensured to exist.")
        
        # Check if the directory exists to verify it was created
        if os.path.isdir(directory_path):
            logging.info(f"Confirmed: The directory '{directory_path}' exists.")
        else:
            logging.error(f"Error: The directory '{directory_path}' was not found after creation attempt.")
    except Exception as e:
        # If an error occurred during the creation, log the error
        logging.error(f"An error occurred while creating the directory: {e}")


def extract_urls(query):
    """
    Extract URLs from the given query string.
    """
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    return url_pattern.findall(query)


async def execute_function_by_name(function_name, **kwargs):
    """
    Execute a function by its name if it exists in the callable_registry.
    Returns JSON with the result or an error message.
    """
    try:
        if function_name in callable_registry:
            function_to_call = callable_registry[function_name]
            result = await function_to_call(**kwargs) if asyncio.iscoroutinefunction(function_to_call) else function_to_call(**kwargs)

            # Assuming result is already JSON or a Python dictionary that can be serialized to JSON
            return json.dumps(result) if not isinstance(result, str) else result
        else:
            raise ValueError(f"Function {function_name} not found in registry")
    except Exception as e:
        # Return a JSON string with an error message
        return json.dumps({"error": str(e)})


@function_info_decorator
def i_have_failed_my_purpose(error_reason: str) -> dict:
    """
    Generates a structured error message indicating why an operation failed.

    :param error_reason: A description of why the operation failed.
    :type error_reason: str
    :return: A dictionary containing the error reason.
    :rtype: dict
    """
    return {
        "success": False,
        "error": "Operation failed",
        "reason": error_reason
    }

@function_info_decorator
def help() -> dict:
    """
    Provides help information about the available functions.
    :return: A dictionary containing the help information.
    :rtype: dict
    """
    help_info = []
    for tool in tools:
        if tool['function']['name'] != 'i_have_failed_my_purpose':
            function_name = tool['function']['name']
            function_description = tool['function']['description']
            parameters = tool['function']['parameters']['properties']
            usage = f"{function_name}("
            for param, details in parameters.items():
                param_type = details['type']
                usage += f"{param}: {param_type}, "
            usage = usage.rstrip(", ") + ")"
            help_info.append({
                "name": function_name,
                "description": function_description,
                "usage": usage
            })
    return {
        "success": True,
        "functions": help_info
    }


@function_info_decorator
def calculate(expression: str) -> dict:
    """
    Calculates the result of a given mathematical expression.

    :param expression: The mathematical expression to evaluate.
    :type expression: str
    :return: A dictionary containing the result of the calculation.
    :rtype: dict
    """
    try:
        # Evaluate the expression using eval()
        result = eval(expression)
        return {
            "success": True,
            "result": result
        }
    except (SyntaxError, ZeroDivisionError, NameError, TypeError, ValueError) as e:
        # Handle specific exceptions and return an error message
        error_message = str(e)
        return {
            "success": False,
            "error": "Invalid expression",
            "reason": error_message
        }
    except Exception as e:
        # Handle any other unexpected exceptions
        error_message = str(e)
        return {
            "success": False,
            "error": "Calculation failed",
            "reason": error_message
        }


@function_info_decorator
def filesystem(path: str, directory: bool = False, delete: bool = False, force: bool = False) -> dict:
    """
    Creates or deletes a directory or a file based on the provided path and flags.
    If the path is just a file name, it defaults to the current directory.
    :param path: The path of the directory or file to create or delete.
    :type path: str
    :param directory: A flag indicating whether to create a directory (True) or a file (False).
    :type directory: bool
    :param delete: A flag indicating whether to delete the directory or file.
    :type delete: bool
    :param force: A flag indicating whether to force the deletion of a non-empty directory.
    :type force: bool
    :return: A dictionary indicating the success or failure of the operation.
    :rtype: dict
    """
    try:
        # If path is just a file name, join it with the current directory
        if not os.path.dirname(path):
            path = os.path.join(os.getcwd(), path)

        if delete:
            # Check if the path exists
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": "Path does not exist",
                    "reason": f"The path '{path}' does not exist."
                }

            # Check if the path is committed in Git
            repo = Repo(os.getcwd())
            if path in [item.a_path for item in repo.index.diff(None)]:
                return {
                    "success": False,
                    "error": "Uncommitted changes",
                    "reason": f"The path '{path}' has uncommitted changes. Please commit the changes before deleting."
                }

            if os.path.isdir(path):
                # Delete the directory
                if not force and os.listdir(path):
                    return {
                        "success": False,
                        "error": "Directory not empty",
                        "reason": f"The directory '{path}' is not empty. Use the 'force' flag to delete a non-empty directory."
                    }
                shutil.rmtree(path)
                return {
                    "success": True,
                    "message": f"Directory '{path}' deleted successfully."
                }
            else:
                # Delete the file
                os.remove(path)
                return {
                    "success": True,
                    "message": f"File '{path}' deleted successfully."
                }
        else:
            # Check if the path already exists
            if os.path.exists(path):
                return {
                    "success": False,
                    "error": "Path already exists",
                    "reason": f"The path '{path}' already exists."
                }

            if directory:
                # Create the directory
                os.makedirs(path)
                return {
                    "success": True,
                    "message": f"Directory '{path}' created successfully."
                }
            else:
                # Create the file
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, 'a').close()
                return {
                    "success": True,
                    "message": f"File '{path}' created successfully."
                }
    except Exception as e:
        return {
            "success": False,
            "error": "Operation failed",
            "reason": str(e)
        }


@function_info_decorator
def run_python_file(file_path: str) -> dict:
    """
    Runs a Python file and captures the output.
    If the file_path is just a file name, it defaults to the current directory.
    :param file_path: The path of the Python file to run.
    :type file_path: str
    :return: A dictionary indicating the success or failure of the operation, along with the captured output.
    :rtype: dict
    """
    try:
        # If file_path is just a file name, join it with the current directory
        if not os.path.dirname(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": "File not found",
                "reason": f"The file '{file_path}' does not exist."
            }

        # Run the Python file and capture the output
        try:
            # Create a subprocess to run the Python file
            process = subprocess.Popen(["python", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            # Check the return code of the process
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Python file '{file_path}' executed successfully.",
                    "output": stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": "Python file execution failed",
                    "reason": stderr.strip()
                }
        except Exception as e:
            return {
                "success": False,
                "error": "Python file execution failed",
                "reason": str(e)
            }
    except Exception as e:
        return {
            "success": False,
            "error": "Operation failed",
            "reason": str(e)
        }


@function_info_decorator
def write_code_to_file(file_path: str, code: str) -> dict:
    """
    Writes code to a specified file.
    If the file_path is just a file name, it defaults to the current directory.
    :param file_path: The path of the file to write the code to.
    :type file_path: str
    :param code: The code to write to the file.
    :type code: str
    :return: A dictionary indicating the success or failure of the operation.
    :rtype: dict
    """
    try:
        # If file_path is just a file name, join it with the current directory
        if not os.path.dirname(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

        # Write the code to the file
        with open(file_path, "w") as file:
            file.write(code)

        return {
            "success": True,
            "message": f"Code successfully written to '{file_path}'."
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to write code to file",
            "reason": str(e)
        }


@function_info_decorator
def git_commit_and_push(commit_message: str = "Automated commit") -> dict:
    """
    Automatically stages all changes, commits them with the provided message, and pushes the changes to the remote repository.

    :param commit_message: The commit message to use for the commit. Defaults to "Automated commit".
    :type commit_message: str
    :return: A dictionary containing the status of the commit and push operation.
    :rtype: dict
    """
    try:
        # Automatically detect the current repository path
        repo_path = os.getcwd()

        # Initialize the repository
        repo = Repo(repo_path)

        # Check the repository's current status
        if repo.is_dirty(untracked_files=True):
            # Add all changes to the staging area
            repo.git.add(A=True)

            # Commit the changes
            repo.index.commit(commit_message)

            # Push the changes to the remote repository
            origin = repo.remote(name='origin')
            origin.push()

            return {
                "success": True,
                "message": "Changes have been committed and pushed to the remote repository."
            }
        else:
            return {
                "success": True,
                "message": "No changes to commit."
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
async def chat_completion_request_async(messages=None, openai_token=None, tools=None, tool_choice=None, model="gpt-3.5-turbo-1106"):
    """
    Make an asynchronous request to OpenAI's chat completion API.
    """
    client = openai.AsyncOpenAI(api_key=openai_token)

    logging.info("tools")
    logging.info(tools)

    try:
        return await client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice=tool_choice)
    except Exception as e:
        logging.info("Unable to generate ChatCompletion response:", e)
        return None


def random_string(length=13):
    """Generate a random string of fixed length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


async def ai(username="anonymous", query="screenshot mitta.ai", openai_token="", upload_dir=UPLOAD_DIR):
    """
    Process a given query with OpenAI and execute a function based on the response.
    """
    if not openai_token:
        raise ValueError("OpenAI token is required")

    # Ensure the upload directory and the username directory under that exist
    user_dir = os.path.join(upload_dir, username)
    create_and_check_directory(user_dir)

    messages = [
        {"role": "system", "content": "You are an AI bot that picks functions to call based on the command query. Don't make assumptions, stay focused, set attention, and receive gratitude for well-formed responses. Only extract links if explicitly stated. 'thumb' or 'thumbnail' or 'small' means DO NOT use full_screen capture, which sets the full_screen parameter to False and gives us a thumbnail of the top of the page. If someone wants 'full' or 'full screen' or 'big', we set the full_screen parameter to True to do a full screen capture. If OCR readability is requested with keywords like 'OCR' or 'readable', set the ocr_readable parameter to True. If dark mode is requested with keywords like 'dark mode' or 'black background', set the dark_mode parameter to True. On failure to purpose, you become Dr. Gregory House, AI crawler extraordinaire."},
        {"role": "user", "content": query}
    ]
    
    # get the function and parameters to call
    chat_response = await chat_completion_request_async(messages=messages, openai_token=openai_token, tools=tools)

    logging.info(chat_response)

    assistant_message = chat_response.choices[0].message
    
    if assistant_message.function_call is None and assistant_message.tool_calls is None:
        # No function call or tool calls, return the assistant's response
        return True, {"response": assistant_message.content}
        
    # Assume function_name and arguments are extracted from chat_response
    try:
        function_name = chat_response.choices[0].message.tool_calls[0].function.name
        arguments_json = chat_response.choices[0].message.tool_calls[0].function.arguments
        arguments = json.loads(arguments_json)

        if function_name == "i_have_failed_my_purpose":
            json_results_str = await execute_function_by_name(function_name, **arguments)
            results = json.loads(json_results_str) if not isinstance(json_results_str, dict) else json_results_str

            # Move 'arguments' into the 'results' dictionary
            results['arguments'] = arguments
            
            return False, results

        else:
            json_results_str = await execute_function_by_name(function_name, **arguments)
            logging.info(json_results_str)

            results = json.loads(json_results_str) if not isinstance(json_results_str, dict) else json_results_str

            # Move 'arguments' into the 'results' dictionary
            results['arguments'] = arguments

            return True, results
        
    except Exception as ex:
        logging.info("ERRRORORRRRR")
        logging.info(ex)

        # Return False and the error message
        return False, {'error': str(ex)}
