import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def search_file(filename: str) -> dict:
    """
    Searches the current directory and all subdirectories for a file with the specified name.
    :param filename: The name of the file to search for.
    :return: A dictionary containing the full path of the file if found, otherwise an error message.
    :rtype: dict
    """
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        if filename in files:
            return {
                "success": True,
                "full_path": os.path.join(root, filename)
            }
    return {
        "success": False,
        "message": f"File '{filename}' not found in directory '{current_dir}'"
    }