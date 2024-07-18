import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def cat_file(file_path: str) -> dict:
    """
    Reads the contents of a file and returns them as a string.
    
    :param file_path: The path of the file to read.
    :type file_path: str
    
    :return: A dictionary containing the success status and the file contents or an error message.
    :rtype: dict
    """
    if not isinstance(file_path, str):
        return {
            "success": False,
            "error": "Invalid input",
            "reason": f"Expected a string for file_path, got {type(file_path).__name__}"
        }
    
    if not file_path:
        return {
            "success": False,
            "error": "Invalid input",
            "reason": "File path cannot be empty"
        }

    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": "File not found",
                "reason": f"The file '{file_path}' does not exist."
            }
        
        # Read the contents of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            contents = file.read()
        
        return {
            "success": True,
            "contents": contents
        }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "reason": f"You do not have permission to read the file '{file_path}'."
        }
    except Exception as e:
        return {
            "success": False,
            "error": "File reading failed",
            "reason": str(e)
        }