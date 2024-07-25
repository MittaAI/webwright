import os
import sys
import string
import random
import re
import hashlib
import logging
from datetime import datetime
from coolname import generate_slug
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

# Constants
WEBWRIGHT_DIR = os.path.expanduser('~/.webwright')
LOG_DIR = os.path.join(WEBWRIGHT_DIR, 'logs')
FUNC_LOG_DIR = os.path.join(LOG_DIR, 'function_logs')

# Ensure necessary directories exist
os.makedirs(WEBWRIGHT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(FUNC_LOG_DIR, exist_ok=True)

def setup_main_logging(log_level=logging.INFO):
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(LOG_DIR, 'webwright.log'), encoding='utf-8'),
        ]
    )
    return logging.getLogger(__name__)

def get_logger():
    return logging.getLogger(__name__)

def setup_function_logging(function_name, log_level=logging.INFO):
    logger = logging.getLogger(function_name)
    logger.setLevel(log_level)
    if not logger.handlers:
        fh = logging.FileHandler(os.path.join(FUNC_LOG_DIR, f'{function_name}.log'), encoding='utf-8')
        fh.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

logger = setup_main_logging()

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
    diff_dir = os.path.join(WEBWRIGHT_DIR, 'diffs')
    create_and_check_directory(diff_dir)
    return diff_dir

def store_diff(diff: str, file_path: str):
    diff_dir = ensure_diff_dir_exists()
    file_hash = calculate_file_hash(file_path)
    if file_hash is None:
        logger.error(f"Failed to calculate hash for {file_path}. Cannot store diff.")
        return None
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

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {str(e)}")
        return None

def format_response(response):
    if response is None:
        return FormattedText([('class:error', "No response to format.\n")])
    
    formatted_text = []
    lines = response.split('\n')
    in_code_block = False
    tag_stack = []
    code_lines = []
    
    math_pattern = re.compile(r'\\\(.*?\\\)')
    tag_pattern = re.compile(r'<(\w+)>|</(\w+)>')
    inline_code_pattern = re.compile(r'(`.*?`|``.*?``)')

    in_html_block = False

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
        
        # Check for <html> tags and handle them separately
        if '<html>' in line:
            in_html_block = True
            formatted_text.append(('class:html', line + '\n'))
            continue
        if '</html>' in line:
            in_html_block = False
            formatted_text.append(('class:html', line + '\n'))
            continue
        if in_html_block:
            formatted_text.append(('class:html', line + '\n'))
            continue

        remaining_line = line
        while (match := tag_pattern.search(remaining_line)):
            opening_tag, closing_tag = match.groups()
            start, end = match.span()
            if opening_tag:
                tag_stack.append(opening_tag)
                if start > 0:
                    formatted_text.append((f'class:{tag_stack[-2] if len(tag_stack) > 1 else ""}', remaining_line[:start]))
                remaining_line = remaining_line[end:]
            elif closing_tag and tag_stack and tag_stack[-1] == closing_tag:
                tag_stack.pop()
                if start > 0:
                    formatted_text.append((f'class:{closing_tag}', remaining_line[:start]))
                remaining_line = remaining_line[end:]
                # Add a linefeed and switch to the default style for any following text
                if remaining_line.strip():
                    formatted_text.append(('', '\n'))
            else:
                remaining_line = remaining_line[end:]
        
        # Apply formatting based on current tag context
        current_class = f'class:{tag_stack[-1]}' if tag_stack else ''
        
        if remaining_line.startswith('#'):
            formatted_text.append(('class:header', remaining_line + '\n'))
        else:
            parts = re.split(r'(\*\*.*?\*\*|`.*?`|``.*?``|\\\(.*?\\\))', remaining_line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    formatted_text.append((f'{current_class} class:bold', part[2:-2]))
                elif inline_code_pattern.match(part):
                    # Handle both single and double ticks
                    code_content = part[1:-1] if part.startswith('`') else part[2:-2]
                    formatted_text.append((f'{current_class} class:inline-code', code_content))
                elif math_pattern.match(part):
                    formatted_text.append((f'{current_class} class:math', part[2:-2]))
                else:
                    formatted_text.append((current_class, part))
            
            formatted_text.append((current_class, '\n'))
    
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
    'html': '#ansiblue underline italic',
})