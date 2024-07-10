import os
import string
import random
from configparser import ConfigParser
import getpass

from coolname import generate_slug

import re
from prompt_toolkit.formatted_text import FormattedText
import logging

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
    config.set(section, key, value)
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
#                                OpenAI Setup                                 #
###############################################################################
from openai import OpenAI

def check_openai_token(openai_token):
    client = OpenAI(api_key=openai_token)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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
    while not openai_token:
        openai_token = input("Please enter your OpenAI API key: ")
        if check_openai_token(openai_token):
            set_config_value("config", "OPENAI_API_KEY", openai_token)
        else:
            print("Invalid token. Please try again.")
            openai_token = None
    return openai_token

def set_openai_api_key(api_key):
    set_config_value("config", "OPENAI_API_KEY", api_key)


###############################################################################
#                               Anthropic Setup                               #
###############################################################################
import anthropic

def get_openai_api_key():
    openai_token = os.getenv("OPENAI_API_KEY") or get_config_value("config", "OPENAI_API_KEY")
    while not openai_token:
        openai_token = input_dialog(
            title="OpenAI API Key",
            text="Please enter your OpenAI API key:"
        ).run()
        if openai_token:
            set_config_value("config", "OPENAI_API_KEY", openai_token)
        else:
            print("Invalid token. Please try again.")
            openai_token = None
    return openai_token


def get_anthropic_api_key():
    anthropic_token = os.getenv("ANTHROPIC_API_KEY") or get_config_value("config", "ANTHROPIC_API_KEY")
    while not anthropic_token:
        anthropic_token = input_dialog(
            title="Anthropic API Key",
            text="Please enter your Anthropic API key:"
        ).run()
        if check_anthropic_token(anthropic_token):
            set_config_value("config", "ANTHROPIC_API_KEY", anthropic_token)
        else:
            print("Invalid token. Please try again.")
            anthropic_token = None
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
            formatted_text.append(('class:header', line[level:].trip() + '\n'))
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

# Initialize configuration
read_config()