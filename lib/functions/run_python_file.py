# lib/functions/run_python_file.py
import os
import subprocess
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def run_python_file(file_path: str) -> dict:
    """
    Runs a Python file and captures the output.
    If the file_path is just a file name, it defaults to the current directory.

    :param file_path: The path of the Python file to run.
    :type file_path: str
    :return: A dictionary indicating the success or failure of the operation, along with the captured output.
    :rtype: dict
    """
    try:
        # If file_path is just a file name, join it with the current directory
        if not os.path.dirname(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": "File not found",
                "reason": f"The file '{file_path}' does not exist."
            }

        # Run the Python file and capture the output
        try:
            # Create a subprocess to run the Python file
            process = subprocess.Popen(["python", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            # Check the return code of the process
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Python file '{file_path}' executed successfully.",
                    "output": stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": "Python file execution failed",
                    "reason": stderr.strip()
                }
        except Exception as e:
            return {
                "success": False,
                "error": "Python file execution failed",
                "reason": str(e)
            }
    except Exception as e:
        return {
            "success": False,
            "error": "Operation failed",
            "reason": str(e)
        }
