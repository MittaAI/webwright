# lib/functions/filesystem.py
import os
import shutil
from git import Repo
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def filesystem(path: str, directory: bool = False, delete: bool = False, force: bool = False) -> dict:
    """
    Creates or deletes a directory or a file based on the provided path and flags.
    If the path is just a file name, it defaults to the current directory.
    :param path: The path of the directory or file to create or delete.
    :type path: str
    :param directory: A flag indicating whether to create a directory (True) or a file (False).
    :type directory: bool
    :param delete: A flag indicating whether to delete the directory or file.
    :type delete: bool
    :param force: A flag indicating whether to force the deletion of a non-empty directory.
    :type force: bool
    :return: A dictionary indicating the success or failure of the operation.
    :rtype: dict
    """
    try:
        # If path is just a file name, join it with the current directory
        if not os.path.dirname(path):
            path = os.path.join(os.getcwd(), path)

        if delete:
            # Check if the path exists
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": "Path does not exist",
                    "reason": f"The path '{path}' does not exist."
                }

            # Check if the path is committed in Git
            repo = Repo(os.getcwd())
            if path in [item.a_path for item in repo.index.diff(None)]:
                return {
                    "success": False,
                    "error": "Uncommitted changes",
                    "reason": f"The path '{path}' has uncommitted changes. Please commit the changes before deleting."
                }

            if os.path.isdir(path):
                # Delete the directory
                if not force and os.listdir(path):
                    return {
                        "success": False,
                        "error": "Directory not empty",
                        "reason": f"The directory '{path}' is not empty. Use the 'force' flag to delete a non-empty directory."
                    }
                shutil.rmtree(path)
                return {
                    "success": True,
                    "message": f"Directory '{path}' deleted successfully."
                }
            else:
                # Delete the file
                os.remove(path)
                return {
                    "success": True,
                    "message": f"File '{path}' deleted successfully."
                }
        else:
            # Check if the path already exists
            if os.path.exists(path):
                return {
                    "success": False,
                    "error": "Path already exists",
                    "reason": f"The path '{path}' already exists."
                }

            if directory:
                # Create the directory
                os.makedirs(path)
                return {
                    "success": True,
                    "message": f"Directory '{path}' created successfully."
                }
            else:
                # Create the file
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, 'a').close()
                return {
                    "success": True,
                    "message": f"File '{path}' created successfully."
                }
    except Exception as e:
        return {
            "success": False,
            "error": "Operation failed",
            "reason": str(e)
        }
