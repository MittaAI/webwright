import os
import fnmatch
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def search_file(filename: str, directory: str = None) -> dict:
    """
    Searches the specified directory (or current directory if not specified) for files or directories matching the specified partial name.
    If a directory is found, lists all files and subdirectories within it.
    
    :param filename: The partial name of the file or directory to search for.
    :param directory: The directory to start the search from.
    :return: A dictionary containing a list of full paths for matching files or directories, or the contents of the found directories.
    :rtype: dict
    """
    if directory is None:
        directory = os.getcwd()
    matches = []
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and similar directories
        if "__pycache__" in root:
            continue
        
        # Search for files
        for file in fnmatch.filter(files, f"*{filename}*"):
            matches.append(os.path.join(root, file))
        
        # Search for directories and list their contents
        for dir in fnmatch.filter(dirs, f"*{filename}*"):
            dir_path = os.path.join(root, dir)
            matches.append(f"Directory: {dir_path}")
            for sub_root, sub_dirs, sub_files in os.walk(dir_path):
                if "__pycache__" in sub_root:
                    continue
                for sub_file in sub_files:
                    matches.append(os.path.join(sub_root, sub_file))
                for sub_dir in sub_dirs:
                    matches.append(os.path.join(sub_root, sub_dir))
    
    if matches:
        return {
            "success": True,
            "matches": matches
        }
    return {
        "success": False,
        "message": f"No files or directories matching '{filename}' found in directory '{directory}'"
    }