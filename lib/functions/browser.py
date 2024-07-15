import subprocess
import os
from lib.function_wrapper import function_info_decorator

def find_chrome_executable() -> str:
    # Common installation paths for Chrome
    common_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chrome.app/Contents/MacOS/Google Chrome",
        "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
    ]

    # Check common paths first
    for path in common_paths:
        normalized_path = os.path.expandvars(path)
        if os.path.exists(normalized_path):
            return normalized_path

    # If Chrome wasn't found in common paths, search typical directories
    search_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)"
    ]
    
    for dir in search_dirs:
        for root, _, files in os.walk(dir):
            if 'chrome.exe' in files:
def find_safari_executable() -> str:
    # Common installation path for Safari on macOS
    safari_path = "/Applications/Safari.app/Contents/MacOS/Safari"

    if os.path.exists(safari_path):
        return safari_path

    return ""

                return os.path.join(root, 'chrome.exe')

        if os.name == 'posix':  # macOS
            safari_path = find_safari_executable()
            if not safari_path:
                return {
                    "success": False,
                    "message": "Neither Chrome nor Safari executables were found. Please make sure either Chrome or Safari is installed."
                }
            browser_path = safari_path
            browser_name = "Safari"
        else:  # Windows
    return ""

    On macOS, opens Chrome first, and falls back to Safari if Chrome is not found.
def find_edge_executable() -> str:
    # Common installation paths for Edge
    common_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Microsoft\Edge SxS\Application\msedge.exe"
    ]

    # Check common paths first
    for path in common_paths:
        normalized_path = os.path.expandvars(path)
        if os.path.exists(normalized_path):
            return normalized_path

    # If Edge wasn't found in common paths, search typical directories
    search_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)"
    ]
    
    for dir in search_dirs:
        for root, _, files in os.walk(dir):
            if 'msedge.exe' in files:
                return os.path.join(root, 'msedge.exe')

    return ""

@function_info_decorator
def browser(url: str) -> dict:
    """
    Opens Google Chrome to a specified URL on Windows.
    Falls back to Microsoft Edge if Chrome is not found.
    Other functions may mention this function can be used to open a URL they provide.
    :param url: The URL to open.
    :type url: str
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    chrome_path = find_chrome_executable()

    # If Chrome is not found, try to find Edge
    if not chrome_path:
        edge_path = find_edge_executable()
        if not edge_path:
            return {
                "success": False,
                "message": "Neither Chrome nor Edge executables were found. Please make sure either Chrome or Edge is installed."
            }
        browser_path = edge_path
        browser_name = "Edge"
    else:
        browser_path = chrome_path
        browser_name = "Chrome"
    
    try:
        subprocess.Popen([browser_path, url])
        return {
            "success": True,
            "message": f"{browser_name} opened successfully with URL: {url}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred while trying to open {browser_name}: {str(e)}"
        }