import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def write_code_to_files(file_path: str, code: str, is_standalone: bool = False) -> dict:
    """
    1. Writes code to a specified file, only if the file doesn't exist.
    2. If the file exists, refuses to update and suggests using apply_code_diff_to_file.
    3. If the file_path is just a file name, it defaults to the current directory.
    4. If is_standalone is True, it saves the file in a temporary directory under ~/.webwright/code_fragments/
       instead of the current directory. Use this for code not directly related to the current codebase.
    5. Please don't use this function to simply show code or other things to the user. Pay attention!

    :param file_path: The path of the file to write the code to.
    :type file_path: str
    :param code: The code to write to the file.
    :type code: str
    :param is_standalone: Whether the code is standalone and should be saved in a temporary directory. Defaults to False.
    :type is_standalone: bool
    :return: A dictionary indicating the success or failure of the operation.
    :rtype: dict
    """
    try:
        # If is_standalone is True, save in temporary directory
        if is_standalone:
            temp_dir = os.path.expanduser("~/.webwright/code_fragments/")
            file_path = os.path.join(temp_dir, file_path)
        else:
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