import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def get_project_files(project_directory: str = None) -> dict:
    """
    Lists all the files in the specified project directory (or current directory if not specified) and returns them as a directory listing,
    ignoring __pycache__, .git, dot files, and other common non-project files.
    :param project_directory: The path to the project directory. Defaults to the current directory.
    :type project_directory: str
    :return: A dictionary containing the status of the operation and the directory listing.
    :rtype: dict
    """
    try:
        # Set the default project directory to the current directory if not specified
        if project_directory is None:
            project_directory = os.getcwd()

        # Check if the project directory exists
        if not os.path.isdir(project_directory):
            return {
                "success": False,
                "error": "Invalid project directory",
                "reason": f"The directory '{project_directory}' does not exist."
            }
        
        # Define patterns and directories to ignore
        ignore_patterns = [
            '__pycache__',
            '.git',
            '.vscode',
            '.idea',
            'node_modules',
            'venv',
            '.env',
        ]
        
        ignore_extensions = [
            '.pyc',
            '.pyo',
            '.pyd',
            '.DS_Store',
        ]

        # List all the files in the project directory, ignoring specified patterns
        file_list = []
        for root, dirs, files in os.walk(project_directory):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_patterns and not d.startswith('.')]
            
            for file in files:
                if not file.startswith('.') and not any(file.endswith(ext) for ext in ignore_extensions):
                    file_path = os.path.relpath(os.path.join(root, file), project_directory)
                    if not any(pattern in file_path for pattern in ignore_patterns):
                        file_list.append(file_path)
        
        # Generate the directory listing
        directory_listing = "Directory listing:\n"
        for file_path in sorted(file_list):
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