import difflib
import os
import logging
from datetime import datetime
from lib.function_wrapper import function_info_decorator

changelog_path = "/Users/andylegrand/Desktop/Summer24/webwright/changelog.txt"
diff_files_dir_path = "/Users/andylegrand/Desktop/Summer24/webwright/diff_files"

@function_info_decorator
def write_code_to_file(file_path: str, code: str) -> dict:
    """
    Writes code to a specified file. If the file already exists, generates a diff
    and updates the changelog.

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
        diff_filename = None
        if os.path.exists(file_path):
            # Read the original content of the file
            with open(file_path, 'r') as file:
                original_code = file.read()

            # Generate a diff between the original and new code
            diff = difflib.unified_diff(
                original_code.splitlines(keepends=True),
                code.splitlines(keepends=True),
                fromfile='original_code.py',
                tofile='new_code.py'
            )
            diff_text = ''.join(list(diff))

            logging.info(f"Diff text:\n{diff_text}")

            if diff_text:
                # Create a timestamp for the diff file
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                diff_filename = f"{os.path.basename(file_path).split('.')[0]}_{timestamp}_diff.txt"
                diff_file_path = os.path.join(diff_files_dir_path, diff_filename)

                logging.info(f"Writing diff to file: {diff_file_path}")

                # Save the diff to a file
                os.makedirs(diff_files_dir_path, exist_ok=True)
                with open(diff_file_path, 'w') as diff_file:
                    diff_file.write(diff_text)

                # Update the changelog
                with open(changelog_path, 'a') as changelog_file:
                    changelog_file.write(f"Updated {file_path} - {diff_filename}\n")

        # Write the new code to the file
        with open(file_path, "w") as file:
            file.write(code)

        return {
            "success": True,
            "message": f"Code successfully written to '{file_path}'.",
            "diff_file": diff_filename
        }
    except Exception as e:
        logging.error(f"Error writing code to file: {str(e)}")
        return {
            "success": False,
            "error": "Failed to write code to file",
            "reason": str(e)
        }

# Example usage
result = write_code_to_file('/Users/andylegrand/Desktop/untitled folder/print_pi.py', 'print("Hello, World!")')
