import os
import fnmatch
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def search_file(filename: str) -> dict:
    """
    Searches the current directory and all subdirectories for files matching the specified partial name.
    :param filename: The partial name of the file to search for.
    :return: A dictionary containing a list of full paths for matching files if found, otherwise an error message.
    :rtype: dict
    """
    current_dir = os.getcwd()
    matches = []
    for root, dirs, files in os.walk(current_dir):
        if "__pycache__" in root:
            continue
        for file in fnmatch.filter(files, f"*{filename}*"):
            matches.append(os.path.join(root, file))
    if matches:
        return {
            "success": True,
            "matches": matches
        }
    return {
        "success": False,
        "message": f"No files matching '{filename}' found in directory '{current_dir}'"
    }