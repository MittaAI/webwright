from lib.function_wrapper import function_info_decorator
import subprocess
import os

@function_info_decorator
def browser(url: str) -> dict:
    """
    Opens Google Chrome to a specified URL on Windows.
    :param url: The URL to open in Chrome.
    :type url: str
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    
    if not os.path.exists(chrome_path):
        return {
            "success": False,
            "message": "Chrome executable not found. Please make sure Chrome is installed in the default location."
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