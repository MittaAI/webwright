import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def write_code_to_file_patch(file_path: str, code: str) -> dict:
    """
    1. Writes code to a specified file, if the file doesn't exist. 
    2. If the file exists, refuses to update and suggests using create_code_diff_and_apply.
    3. If the file_path is just a file name, it defaults to the current directory.
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

        # Check if the file already exists
        if os.path.exists(file_path):
            return {
                "success": False,
                "message": f"File '{file_path}' already exists. Please use the create_code_diff_and_apply function to update existing files."
            }

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

        # Write the code to the file with UTF-8 encoding
        with open(file_path, "w", encoding="utf-8") as file:
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