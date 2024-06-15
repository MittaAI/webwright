import os
from lib.function_wrapper import function_info_decorator
from lib.util import list_files

@function_info_decorator
def get_project_files(project_directory: str) -> dict:
    """
    Lists all the files in the project directory and returns them as a directory listing.
    :param project_directory: The path to the project directory.
    :type project_directory: str
    :return: A dictionary containing the status of the operation and the directory listing.
    :rtype: dict
    """
    try:
        # Check if the project directory exists
        if not os.path.isdir(project_directory):
            return {
                "success": False,
                "error": "Invalid project directory",
                "reason": f"The directory '{project_directory}' does not exist."
            }
        
        # List all the files in the project directory
        file_list = list_files(project_directory)
        
        # Generate the directory listing
        directory_listing = "Directory listing:\n"
        for file_path in file_list:
            directory_listing += f"{file_path}\n"
        
        return {
            "success": True,
            "message": "Project files listed successfully",
            "directory_listing": directory_listing
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to list project files",
            "reason": str(e)
        }