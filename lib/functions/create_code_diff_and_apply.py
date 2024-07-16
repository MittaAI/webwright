import os
from datetime import datetime
from lib.function_wrapper import function_info_decorator
import difflib

@function_info_decorator
def create_code_diff(diff: str, file_path: str) -> dict:
    """
    1. Takes a diff string and a file path as input.
    2. Saves the diff to the user's .webwright directory.
    3. Applies the diff to the specified file using difflib.
    4. Logs the diff in the changelog in the user's .webwright directory.
    :param diff: The diff string containing the changes to apply.
    :type diff: str
    :param file_path: The path of the file to apply the diff to.
    :type file_path: str
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    try:
        # Step 1: Input is already handled by function parameters

        # Step 2: Save the diff to the user's .webwright directory
        webwright_dir = os.path.expanduser('~/.webwright')
        diff_dir = os.path.join(webwright_dir, 'diffs')
        os.makedirs(diff_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        diff_filename = f"{os.path.basename(file_path).split('.')[0]}_{timestamp}_diff.txt"
        diff_file_path = os.path.join(diff_dir, diff_filename)
        
        with open(diff_file_path, 'w') as diff_file:
            diff_file.write(diff)

        # Step 3: Apply the diff to the specified file using difflib
        with open(file_path, "r") as file:
            original_contents = file.read()

        # Parse the unified diff
        patch = difflib.unified_diff(original_contents.splitlines(keepends=True), 
                                     original_contents.splitlines(keepends=True), 
                                     n=0)
        patch = list(patch)[2:]  # Remove the header lines

        # Apply the parsed diff
        patched_contents = difflib.patch(original_contents.splitlines(keepends=True), patch)

        # Write the patched contents back to the file
        with open(file_path, "w") as file:
            file.writelines(patched_contents)

        # Step 4: Log the diff in the changelog
        changelog_path = os.path.join(webwright_dir, 'changelog.txt')
        with open(changelog_path, 'a') as changelog_file:
            changelog_file.write(f"{timestamp}: Applied diff {diff_filename} to {file_path}\n")

        return {
            "success": True,
            "message": f"Successfully applied diff to {file_path} and saved as {diff_filename}",
            "diff_file": diff_filename
        }
    except FileNotFoundError:
        return {
            "success": False, 
            "message": f"File not found at path: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred while applying diff: {str(e)}"
        }