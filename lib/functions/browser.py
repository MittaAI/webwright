import subprocess
import os
from lib.function_wrapper import function_info_decorator

def find_chrome_executable() -> str:
    # Common installation paths for Chrome
    common_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
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
                return os.path.join(root, 'chrome.exe')

    return ""

@function_info_decorator
def browser(url: str) -> dict:
    """
    Opens Google Chrome to a specified URL on Windows.
    :param url: The URL to open in Chrome.
    :type url: str
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    chrome_path = find_chrome_executable()
    
    if not chrome_path:
        return {
            "success": False,
            "message": "Chrome executable not found. Please make sure Chrome is installed."
        }
    
    try:
        subprocess.Popen([chrome_path, url])
        return {
            "success": True,
            "message": f"Chrome opened successfully with URL: {url}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred while trying to open Chrome: {str(e)}"
        }