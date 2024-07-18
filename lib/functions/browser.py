import subprocess
import os
from lib.function_wrapper import function_info_decorator
import platform

def find_chrome_executable() -> str:
    if platform.system() == "Windows":
        # Common installation paths for Chrome on Windows
        common_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"
        ]
    elif platform.system() == "Darwin":  # macOS
        # Common installation paths for Chrome on macOS
        common_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Users/%USERNAME%/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]
    else:
        return ""

    # Check common paths first
    for path in common_paths:
        normalized_path = os.path.expandvars(path)
        if os.path.exists(normalized_path):
            return normalized_path

    if platform.system() == "Windows":
        # If Chrome wasn't found in common paths, search typical directories on Windows
        search_dirs = [
            r"C:\Program Files",
            r"C:\Program Files (x86)"
        ]
        for dir in search_dirs:
            for root, _, files in os.walk(dir):
                if 'chrome.exe' in files:
                    return os.path.join(root, 'chrome.exe')
    elif platform.system() == "Darwin":
        # If Chrome wasn't found in common paths, search typical directories on macOS
        search_dirs = [
            "/Applications",
            "/Users/%USERNAME%/Applications"
        ]
        for dir in search_dirs:
            for root, _, files in os.walk(dir):
                if 'Google Chrome' in files:
                    return os.path.join(root, 'Google Chrome')
    return ""

def find_edge_executable() -> str:
    if platform.system() != "Windows":
        return ""

    # Common installation paths for Edge on Windows
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

def find_safari_executable() -> str:
    if platform.system() == "Darwin":  # macOS
        # Safari should be present on all macOS systems
        return "/Applications/Safari.app/Contents/MacOS/Safari"
    return ""

@function_info_decorator
def browser(url: str) -> dict:
    """
    Opens Google Chrome to a specified URL on Windows or macOS.
    Falls back to Microsoft Edge on Windows and Safari on macOS if Chrome is not found.
    Other functions may mention this function can be used to open a URL they provide.

    Very useful when showing the user URLs.
    
    :param url: The URL to open.
    :type url: str
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    chrome_path = find_chrome_executable()

    if platform.system() == "Darwin":  # macOS
        # If Chrome is not found, try to find Safari on macOS
        if not chrome_path:
            safari_path = find_safari_executable()
            if not safari_path:
                return {
                    "success": False,
                    "message": "Neither Chrome nor Safari executables were found. Please make sure either Chrome or Safari is installed."
                }
            browser_path = safari_path
            browser_name = "Safari"
        else:
            browser_path = chrome_path
            browser_name = "Chrome"
    else:
        # If Chrome is not found, try to find Edge on Windows
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