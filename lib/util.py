import os
import string
import random
import shutil
from configparser import ConfigParser
from coolname import generate_slug

import re
from prompt_toolkit.formatted_text import FormattedText

# Ensure the .webwright directory exists
webwright_dir = os.path.expanduser('~/.webwright')
os.makedirs(webwright_dir, exist_ok=True)

import logging
def setup_logging(log_level=logging.INFO):
    log_dir = os.path.join(webwright_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'webwright.log')),
        ]
    )
    
    # Get the logger for the current module
    logger = logging.getLogger(__name__)
    
    return logger

def get_logger():
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()

# Constants for configuration directory and file
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".webwright")
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, ".webwright_config")

# Initialize configuration parser
config = ConfigParser()

# Function to ensure configuration directory exists
def ensure_config_dir_exists():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

# Function to read configuration file
def read_config():
    ensure_config_dir_exists()
    config.read(CONFIG_FILE_PATH)

# Function to write configuration file
def write_config():
    ensure_config_dir_exists()
    with open(CONFIG_FILE_PATH, "w") as f:
        config.write(f)

# Function to set configuration value
def set_config_value(section, key, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, value)
    write_config()

# Function to get configuration value
def get_config_value(section, key):
    if config.has_option(section, key):
        return config.get(section, key)
    return None

# ensure directory exists
def create_and_check_directory(directory_path):
    try:
        os.makedirs(directory_path, exist_ok=True)
        logging.info(f"Directory '{directory_path}' ensured to exist.")
        if os.path.isdir(directory_path):
            logging.info(f"Confirmed: The directory '{directory_path}' exists.")
        else:
            logging.error(f"Error: The directory '{directory_path}' was not found after creation attempt.")
    except Exception as e:
        logging.error(f"An error occurred while creating the directory: {e}")

def extract_urls(query):
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    return url_pattern.findall(query)

# Function to list files in a directory
def list_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        # Filter out __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            # Filter out .pyc files
            if not (file.endswith(".pyc") or file.startswith(".")):
                file_path = os.path.join(root, file)
                file_list.append(file_path)
    
    return file_list

# Function to generate a random string
def random_string(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# Functions to handle username
def set_username(username):
    set_config_value("config", "username", username)
    return username

def get_username():
    username = get_config_value("config", "username")
    if username:
        print(f"system> You are logged in as `{username}`.")
        return username
    else:
        username = generate_slug(2)
        return set_username(username)

# Function to setup SSH key
def setup_ssh_key():
    saved_ssh_key = get_config_value("config", "SSH_KEY")
    if saved_ssh_key:
        print(f"system> Using saved SSH key: {saved_ssh_key}")
        return

    ssh_directory = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_directory):
        print("system> No SSH keys found.")
        return
    keys = [file for file in os.listdir(ssh_directory) if os.path.isfile(os.path.join(ssh_directory, file)) and not file.endswith(".pub")]
    if not keys:
        print("system> No SSH keys found.")
        return
    print("system> Available SSH keys:")
    for i, key in enumerate(keys, start=1):
        print(f"{i}. {key}")
    while True:
        try:
            choice = int(input("system> Enter the number of the SSH key to use: "))
            if 1 <= choice <= len(keys):
                selected_key = keys[choice - 1]
                break
            else:
                print("system> Invalid choice. Please try again.")
        except ValueError:
            print("system> Invalid input. Please enter a valid number.")
    ssh_key_path = os.path.join(ssh_directory, selected_key)
    destination_path = os.path.join(CONFIG_DIR, "id_rsa")
    shutil.copy2(ssh_key_path, destination_path)
    set_config_value("config", "SSH_KEY", destination_path)
    print(f"system> SSH key '{selected_key}' has been set up and saved in '{destination_path}'.")

# Functions to handle API keys
def get_openai_api_key():
    openai_token = os.getenv("OPENAI_API_KEY") or get_config_value("config", "OPENAI_API_KEY")
    if not openai_token:
        openai_token = input("system> OpenAI API key not provided. Please enter your OpenAI API key: ")
        set_config_value("config", "OPENAI_API_KEY", openai_token)
    return openai_token

def set_openai_api_key(api_key):
    set_config_value("config", "OPENAI_API_KEY", api_key)

def get_anthropic_api_key():
    anthropic_token = os.getenv("ANTHROPIC_API_KEY") or get_config_value("config", "ANTHROPIC_API_KEY")
    if not anthropic_token:
        anthropic_token = input("system> Anthropic API key not provided. Please enter your Anthropic API key: ")
        set_config_value("config", "ANTHROPIC_API_KEY", anthropic_token)
    return anthropic_token

def set_anthropic_api_key(api_key):
    set_config_value("config", "ANTHROPIC_API_KEY", api_key)

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
        
        # Handle headers
        if line.startswith('#'):
            level = len(line.split()[0])
            formatted_text.append(('class:header', line[level:].strip() + '\n'))
            continue
        
        # Handle bold text, inline code, and math expressions
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

# Initialize configuration
read_config()
