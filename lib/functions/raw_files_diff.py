import difflib
import logging
from lib.function_wrapper import function_info_decorator

logger = logging.getLogger(__name__)

@function_info_decorator

def raw_files_diff(file1_path: str, file2_path: str) -> dict:
    """
    Takes two file paths and returns the raw difference between their contents.

    :param file1_path: Path to the first file
    :param file2_path: Path to the second file
    :return: A dictionary containing the success status, and the raw difference or an error message.
    """
    try:
        with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
            file1_lines = file1.readlines()
            file2_lines = file2.readlines()
        
        diff = difflib.unified_diff(file1_lines, file2_lines, fromfile=file1_path, tofile=file2_path)
        diff_output = ''.join(diff)
        if diff_output:
            return {
                "success": True,
                "message": f"Differences found between {file1_path} and {file2_path}.",
                "diff": diff_output
            }
        else:
            return {
                "success": True,
                "message": f"No differences found between {file1_path} and {file2_path}."
            }
    except FileNotFoundError as e:
        error_message = f"File not found: {str(e)}"
        logger.error(error_message, exc_info=True)
        return {
            "success": False,
            "error": error_message
        }
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message, exc_info=True)
        return {
            "success": False,
            "error": error_message
        }
