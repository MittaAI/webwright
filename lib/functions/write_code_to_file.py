# lib/functions/write_code_to_file.py
import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def write_code_to_file(file_path: str, code: str) -> dict:
    """
    Writes code to a specified file.
    If the file_path is just a file name, it defaults to the current directory.
    You can use matplot to do graphs, but they should be run with run_python_file_non_blocking
    If you write code, you should offer to show it. If it's short, you can show it before asking.
    
    :param file_path: The path of the file to write the code to.
    :type file_path: str
    :param code: The code to write to the file.
    :type code: str
    :return: A dictionary indicating the success or failure of the operation.
    :rtype: dict
    """
    try:
        # If file_path is just a file name, join it with the current directory
        if not os.path.dirname(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

        # Write the code to the file
        with open(file_path, "w") as file:
            file.write(code)

        return {
            "success": True,
            "message": f"Code successfully written to '{file_path}'."
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to write code to file",
            "reason": str(e)
        }
