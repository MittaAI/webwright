import os
import sys

import string
import random
from configparser import ConfigParser
import getpass
from datetime import datetime

from coolname import generate_slug

import re
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog, yes_no_dialog
from openai import OpenAI
from prompt_toolkit.application import Application
from prompt_toolkit.styles import Style

import logging
import hashlib

# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

# Constants for configuration directory and file
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".webwright")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "webwright_config")

# Initialize configuration parser
config = ConfigParser()

def setup_logging(log_level=logging.INFO):
    log_dir = os.path.join(webwright_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'webwright.log'), encoding='utf-8'),
        ]
    )
    
    return logging.getLogger(__name__)

def get_logger():
    return logging.getLogger(__name__)

logger = setup_logging()

def ensure_config_dir_exists():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def read_config():
    ensure_config_dir_exists()
    config.read(CONFIG_FILE_PATH)

def write_config():
    ensure_config_dir_exists()
    with open(CONFIG_FILE_PATH, "w") as f:
        config.write(f)

def set_config_value(section, key, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, str(value))  # Convert value to string
    write_config()

def get_config_value(section, key):
    if config.has_option(section, key):
        return config.get(section, key)
    return None

def create_and_check_directory(directory_path):
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.info(f"Directory '{directory_path}' ensured to exist.")
        if os.path.isdir(directory_path):
            logger.info(f"Confirmed: The directory '{directory_path}' exists.")
        else:
            logger.error(f"Error: The directory '{directory_path}' was not found after creation attempt.")
    except Exception as e:
        logger.error(f"An error occurred while creating the directory: {e}")

def ensure_diff_dir_exists():
    """Ensure that the diff directory exists within the .webwright folder."""
    diff_dir = os.path.join(webwright_dir, 'diffs')
    create_and_check_directory(diff_dir)
    return diff_dir

def store_diff(diff: str, file_path: str):
    """
    Store the generated diff for a given file in the diffs directory.
    The stored diff filename includes a timestamp and the hash of the original file.
    
    :param diff: The generated diff content.
    :param file_path: The path of the file the diff is associated with.
    :return: The path where the diff file was stored, or None if there was an error.
    :rtype: str or None
    """
    diff_dir = ensure_diff_dir_exists()
    
    # Calculate the hash of the original file
    file_hash = calculate_file_hash(file_path)
    if file_hash is None:
        logger.error(f"Failed to calculate hash for {file_path}. Cannot store diff.")
        return None

    # Generate a unique filename for the diff
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = os.path.basename(file_path)
    diff_file_name = f"{file_name}_{timestamp}_{file_hash}.diff"
    diff_file_path = os.path.join(diff_dir, diff_file_name)
    
    try:
        with open(diff_file_path, 'w') as f:
            f.write(diff)
        logger.info(f"Diff stored for {file_path} at {diff_file_path}")
        return diff_file_path
    except Exception as e:
        logger.error(f"Error storing diff for {file_path}: {str(e)}")
        return None

def extract_urls(query):
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    return url_pattern.findall(query)

def list_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for file in files:
            if not (file.endswith(".pyc") or file.startswith(".")):
                file_path = os.path.join(root, file)
                file_list.append(file_path)
    return file_list

def random_string(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def set_username(username):
    set_config_value("config", "username", username)
    return username

def get_username():
    username = get_config_value("config", "username")
    if username:
        print(f"You are logged in as `{username}`.")
        return username
    else:
        username = generate_slug(2)
        return set_username(username)


###############################################################################
#                                  SSH Setup                                  #
###############################################################################
def configure_git_ssh(ssh_key_path):
    ssh_config_path = os.path.expanduser('~/.ssh/config')
    git_host = 'github.com'  # You can change this for other Git hosts

    config_entry = f"""
Host {git_host}
    IdentityFile {ssh_key_path}
    """

    if not os.path.exists(ssh_config_path):
        with open(ssh_config_path, 'w') as f:
            f.write(config_entry)
        print(f"Created new SSH config file with Git configuration.")
    else:
        with open(ssh_config_path, 'r') as f:
            existing_config = f.read()

        if f"Host {git_host}" not in existing_config:
            with open(ssh_config_path, 'a') as f:
                f.write(config_entry)
            print(f"Added Git SSH configuration to existing SSH config file.")
        else:
            print(f"Git SSH configuration already exists in SSH config file.")

    os.chmod(ssh_config_path, 0o600)
    print(f"Git is now configured to use SSH key: {ssh_key_path}")

def setup_ssh_key():
    saved_ssh_key = get_config_value("config", "SSH_KEY")
    if saved_ssh_key and os.path.exists(saved_ssh_key):
        print(f"Using saved SSH key: {saved_ssh_key}")
        configure_git_ssh(saved_ssh_key)
        return saved_ssh_key

    ssh_directory = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_directory):
        print("No SSH keys found.")
        return None

    keys = [file for file in os.listdir(ssh_directory) if os.path.isfile(os.path.join(ssh_directory, file)) and not file.endswith(".pub")]
    if not keys:
        print("No SSH keys found.")
        return None

    print("Available SSH keys:")
    for i, key in enumerate(keys, start=1):
        print(f"{i}. {key}")

    while True:
        try:
            choice = int(input("Enter the number of the SSH key to use: "))
            if 1 <= choice <= len(keys):
                selected_key = keys[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    ssh_key_path = os.path.join(ssh_directory, selected_key)
    set_config_value("config", "SSH_KEY", ssh_key_path)
    print(f"SSH key '{selected_key}' has been set up at '{ssh_key_path}'.")
    
    configure_git_ssh(ssh_key_path)
    return ssh_key_path

###############################################################################
#                                Gemini Setup                                 #
###############################################################################
import google.generativeai as genai
from prompt_toolkit.shortcuts import input_dialog

def check_gemini_token(gemini_token):
    try:
        genai.configure(api_key=gemini_token)

        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = "Confirm the token is working."
        response = model.generate_content(prompt)

        print("Gemini API token verified successfully.")
        return True

    except Exception as e:
        print(f"Error verifying Gemini API token: {str(e)}")
        return False

def get_gemini_api_key():
    gemini_token = os.getenv("GEMINI_API_KEY") or get_config_value("config", "GEMINI_API_KEY")

    if gemini_token == "NONE":
        return None
    
    if gemini_token and check_gemini_token(gemini_token):
        return gemini_token

    gemini_token = input_dialog(
        title="Gemini API Key",
        text="Enter your Gemini API key (Enter to skip):"
    ).run()

    if gemini_token == '':  # User hit Enter without providing a token
        print("Gemini token entry cancelled.")
        set_config_value("config", "GEMINI_API_KEY", "NONE")
        return None
    
    if gemini_token:
        if check_gemini_token(gemini_token):
            set_config_value("config", "GEMINI_API_KEY", gemini_token)
            return gemini_token
        else:
            print("Invalid Gemini token. Skipping.")
    return None

def set_gemini_api_key(api_key):
    set_config_value("config", "GEMINI_API_KEY", api_key)

###############################################################################
#                                OpenAI Setup                                 #
###############################################################################
from openai import OpenAI

def check_openai_token(openai_token):
    client = OpenAI(api_key=openai_token)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # only used to verify token
            messages=[{"role": "user", "content": "Confirm the token is working."}],
            max_tokens=5
        )
        print("OpenAI API token verified successfully.")
        return True
    except Exception as e:
        print(f"Error verifying OpenAI API token: {str(e)}")
        return False

def get_openai_api_key():
    openai_token = os.getenv("OPENAI_API_KEY") or get_config_value("config", "OPENAI_API_KEY")

    if openai_token == "NONE":
        return None
    
    if openai_token and check_openai_token(openai_token):
        return openai_token

    openai_token = input_dialog(
        title="OpenAI API Key",
        text="Enter your OpenAI API key (Enter to skip):"
    ).run()

    if openai_token == '':  # User hit Enter without providing a token
        print("OpenAI token entry cancelled.")
        set_config_value("config", "OPENAI_API_KEY", "NONE")
        return None
    
    if openai_token:
        if check_openai_token(openai_token):
            set_config_value("config", "OPENAI_API_KEY", openai_token)
            return openai_token
        else:
            print("Invalid OpenAI token. Skipping.")
    return None

def set_openai_api_key(api_key):
    set_config_value("config", "OPENAI_API_KEY", api_key)

# Function to list OpenAI models
def list_openai_models(api_key):
    client = OpenAI(api_key=api_key)
    models = client.models.list()
    return models

# Function to select and set OpenAI model based on a dialog
def select_openai_model(api_key):
    models = list_openai_models(api_key=api_key)
    # Filter to show only gpt models
    model_choices = [(model.id, model.id) for model in models.data if "gpt" in model.id.lower()]
    
    selected_model = radiolist_dialog(
        title="Select OpenAI Model",
        text="Choose an OpenAI model from the list below:",
        values=model_choices
    ).run()
    
    if selected_model:
        set_config_value("config", "OPENAI_MODEL", selected_model)
        print(f"Selected OpenAI model: {selected_model}")
        return selected_model
    else:
        print("No model selected.")
        return None
 

###############################################################################
#                               Anthropic Setup                               #
###############################################################################
import anthropic

def check_anthropic_token(anthropic_token):
    try:
        client = anthropic.Anthropic(api_key=anthropic_token)
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620", # only used to verify token
            max_tokens=10,
            temperature=0,
            system="Respond with 'Token verified' if this message is received.",
            messages=[
                {
                    "role": "user",
                    "content": "Verify token"
                }
            ]
        )
        if "Token verified" in message.content[0].text:
            print("Anthropic API token verified successfully.")
            return True
        else:
            print("Unexpected response from Anthropic API.")
            return False
    except Exception as e:
        print(f"Error verifying Anthropic API token: {str(e)}")
        return False

def get_anthropic_api_key():
    anthropic_token = os.getenv("ANTHROPIC_API_KEY") or get_config_value("config", "ANTHROPIC_API_KEY")
    if anthropic_token == "NONE":
        return None
    
    if anthropic_token and check_anthropic_token(anthropic_token):
        return anthropic_token
    
    anthropic_token = input_dialog(
        title="Anthropic API Key",
        text="Enter your Anthropic API key (Enter to skip):"
    ).run()

    if anthropic_token == '':  # User hit Enter without providing a token
        print("Anthropic token entry cancelled.")
        set_config_value("config", "ANTHROPIC_API_KEY", "NONE")
        return None

    if anthropic_token:
        if check_anthropic_token(anthropic_token):
            set_config_value("config", "ANTHROPIC_API_KEY", anthropic_token)
            return anthropic_token
        else:
            print("Invalid Anthropic token. Skipping.")
    return None

def set_anthropic_api_key(api_key):
    set_config_value("config", "ANTHROPIC_API_KEY", api_key)

# Manual list of Anthropic models
ANTHROPIC_MODELS = [
    ("claude-3-opus-20240229", "Claude 3 Opus"),
    ("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
    ("claude-3-haiku-20240307", "Claude 3 Haiku"),
    ("claude-3-5-sonnet-20240620", "Claude 3.5 Sonnet")
]

# Function to list Anthropic models
def list_anthropic_models():
    return ANTHROPIC_MODELS

# Function to select and set Anthropic model based on a dialog
def select_anthropic_model():
    model_choices = list_anthropic_models()
    
    selected_model = radiolist_dialog(
        title="Select Anthropic Model",
        text="Choose an Anthropic model from the list below:",
        values=model_choices
    ).run()
    
    if selected_model:
        set_config_value("config", "ANTHROPIC_MODEL", selected_model)
        print(f"Selected Anthropic model: {selected_model}")
        return selected_model
    else:
        print("No model selected.")
        return None

def determine_api_to_use():
    preferred_api = get_config_value("config", "PREFERRED_API")

    openai_token = get_openai_api_key()
    anthropic_token = get_anthropic_api_key()
    
    openai_model = get_config_value("config", "OPENAI_MODEL")
    anthropic_model = get_config_value("config", "ANTHROPIC_MODEL")
    
    if not openai_model or openai_model == "NONE":
        openai_model = select_openai_model(api_key=openai_token)
    
    if not anthropic_model or anthropic_model == "NONE":
        anthropic_model = select_anthropic_model()

    # Check if the preferred API is set and its token is valid
    if preferred_api == "openai" and openai_token:
        print(f"Using preferred API: OpenAI with model {openai_model}")
        return "openai", openai_token, None, openai_model
    elif preferred_api == "anthropic" and anthropic_token:
        print(f"Using preferred API: Anthropic with model {anthropic_model}")
        return "anthropic", None, anthropic_token, anthropic_model
    
    # If preferred API is not set or its token is invalid, proceed with selection logic
    if openai_token and anthropic_token:
        try:
            choice = radiolist_dialog(
                title="Choose API",
                text="Both OpenAI and Anthropic APIs are available. Which one would you like to use?",
                values=[
                    ("openai", f"OpenAI ({openai_model})"),
                    ("anthropic", f"Anthropic ({anthropic_model})")
                ]
            ).run()
            
            if choice is None:  # User cancelled the dialog
                print("API selection cancelled. Exiting program.")
                return None, None, None, None
            
            set_config_value("config", "PREFERRED_API", str(choice))
            if choice == "openai":
                return choice, openai_token, None, openai_model
            else:
                return choice, None, anthropic_token, anthropic_model
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                # Restart the event loop
                application = Application()
                application.run()
                return determine_api_to_use()  # Try again
            else:
                raise  # Re-raise if it's a different RuntimeError
    elif openai_token:
        print(f"Using OpenAI API with model {openai_model}")
        set_config_value("config", "PREFERRED_API", "openai")
        return "openai", openai_token, None, openai_model
    elif anthropic_token:
        print(f"Using Anthropic API with model {anthropic_model}")
        set_config_value("config", "PREFERRED_API", "anthropic")
        return "anthropic", None, anthropic_token, anthropic_model
    else:
        print("Error: Neither OpenAI nor Anthropic API key is set.")
        try:
            should_exit = yes_no_dialog(
                title="Exit Program",
                text="Can't proceed without tokens. Edit your ~/.webwright/webwright_config file to set the API key(s). Exit program?"
            ).run()
            if should_exit:
                return None, None, None, None
            else:
                return determine_api_to_use()  # Recursively call to try again
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                # Restart the event loop
                application = Application()
                application.run()
                return determine_api_to_use()  # Try again
            else:
                raise  # Re-raise if it's a different RuntimeError

# Github setup
def get_github_token():
    """
    Attempts to retrieve the GitHub token first from environment variables, then from configuration.

    Returns:
        dict: A dictionary containing the token (if retrieved successfully) and any error messages.
    """
    
    from github import Github

    # First, try to get the GitHub token from the environment variable
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        # Test if the token works with GitHub
        try:
            g = Github(github_token)
            g.get_user().login  # Attempt to retrieve the username to confirm token is valid
            return {"token": github_token, "error": None}
        except Exception as e:
            error_message = f"Environment GitHub token failed: {e}"
            logger.warning(error_message)
            # Continue to attempt to retrieve from config if environment token fails

    # If the environment variable fails, attempt to get the GitHub token from the configuration
    try:
        github_token = get_config_value("config", "GITHUB_API_TOKEN")
        # Test if the new token works with GitHub
        try:
            g = Github(github_token)
            g.get_user().login
            return {"token": github_token, "error": None}
        except Exception as e:
            error_message = f"Config GitHub token failed: {e}"
            logger.error(error_message)
            return {"token": None, "error": error_message}
    except Exception as e:
        error_message = f"Failed to load GitHub token from config: {e}"
        logger.error(error_message)
        return {"token": None, "error": error_message}

    # If no token could be retrieved
    return {"token": None, "error": "GitHub token not available from both environment and config."}

def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {str(e)}")
        return None

# Response formatting
def format_response(response):
    if response is None:
        return FormattedText([('class:error', "No response to format.\n")])
    
    formatted_text = []
    lines = response.split('\n')
    in_code_block = False
    in_thinking_block = False
    code_lines = []
    
    math_pattern = re.compile(r'\\\(.*?\\\)')

    for line in lines:
        if line.startswith('```'):
            if in_code_block:
                in_code_block = False
                formatted_text.append(('class:code', ''.join(code_lines)))
                code_lines = []
            else:
                in_code_block = True
            continue
        
        if in_code_block:
            code_lines.append(line + '\n')
            continue
        
        if line.startswith('<thinking>'):
            in_thinking_block = True
            formatted_text.append(('class:thinking', line[10:] + '\n'))
            continue
        elif line.startswith('</thinking>'):
            in_thinking_block = False
            continue
        
        if in_thinking_block:
            formatted_text.append(('class:thinking', line + '\n'))
            continue
        
        if line.startswith('#'):
            level = len(line.split()[0])
            formatted_text.append(('class:header', line[level:].strip() + '\n'))
            continue
        
        parts = re.split(r'(\*\*.*?\*\*|`.*?`|\\\(.*?\\\))', line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                formatted_text.append(('class:bold', part[2:-2]))
            elif part.startswith('`') and part.endswith('`'):
                formatted_text.append(('class:inline-code', part[1:-1]))
            elif math_pattern.match(part):
                formatted_text.append(('class:math', part[2:-2]))  
            else:
                formatted_text.append(('', part))
        
        formatted_text.append(('', '\n'))
    
    return FormattedText(formatted_text)

# Styles
custom_style = Style.from_dict({
    'code': '#ansicyan',
    'header': '#ansigreen bold',
    'thinking': '#ansiblue italic',
    'bold': 'bold',
    'inline-code': '#ansiyellow',
    'error': '#ansired bold',
    'warning': '#ansiyellow',
    'success': '#ansigreen',
    'math': '#ansimagenta',
    'emoji': '#ansibrightmagenta',
    'username': '#ansigreen bold',
    'model': '#ansiyellow bold',
    'path': '#ansicyan',
    'instruction': '#ansibrightgreen',
})

# Initialize configuration
read_config()
