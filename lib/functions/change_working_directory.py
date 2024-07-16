import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def change_working_directory(new_directory: str) -> dict:
    """
    Changes the current working directory of the application.
    
    :param new_directory: The path to the new working directory.
    :type new_directory: str
    :return: A dictionary indicating the success or failure of the operation.
    :rtype: dict
    """
    try:
        os.chdir(new_directory)
        return {
            "success": True,
            "message": f"Successfully changed the working directory to '{new_directory}'."
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to change the working directory",
            "reason": str(e)
        }
