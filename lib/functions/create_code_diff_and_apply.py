import os
from datetime import datetime
from lib.function_wrapper import function_info_decorator
import logging
from typing import List
import difflib
import re

def add_line_numbers_to_diff(original_content: str, diff_content: str) -> str:
    original_lines = original_content.splitlines()
    diff_lines = diff_content.splitlines()
    numbered_diff_lines = []
    original_line_num = 1
    new_line_num = 1

    for line in diff_lines:
        if line.startswith('---') or line.startswith('+++'):
            numbered_diff_lines.append(line)
        elif line.startswith('@@'):
            # Replace placeholder or incorrect line numbers with accurate ones
            hunk_start = len(numbered_diff_lines)
            numbered_diff_lines.append(f"@@ -{original_line_num},0 +{new_line_num},0 @@")
        elif line.startswith('-'):
            original_line_num += 1
        elif line.startswith('+'):
            new_line_num += 1
        else:  # Context line
            original_line_num += 1
            new_line_num += 1
        
        numbered_diff_lines.append(line)

    # Update the hunk headers with correct line counts
    for i, line in enumerate(numbered_diff_lines):
        if line.startswith('@@'):
            original_count = 0
            new_count = 0
            for hunk_line in numbered_diff_lines[i+1:]:
                if hunk_line.startswith('@@'):
                    break
                if hunk_line.startswith('-'):
                    original_count += 1
                elif hunk_line.startswith('+'):
                    new_count += 1
                elif not hunk_line.startswith('\\'):  # Ignore "\ No newline at end of file"
                    original_count += 1
                    new_count += 1
            numbered_diff_lines[i] = f"@@ -{original_line_num-original_count},{original_count} +{new_line_num-new_count},{new_count} @@"

    return '\n'.join(numbered_diff_lines)

@function_info_decorator
def create_code_diff_and_apply(diff: str, file_path: str) -> dict:
    """
    Applies a diff to a file and logs changes.

    LLM Instructions:
    - Generate diffs WITHOUT line numbers or chunk headers (e.g., @@ -7,7 +7,7 @@).
    - Use simple diff format:
      '-' for removed lines
      '+' for added lines
      ' ' for context (unchanged) lines
    - Function handles line numbering internally.
    - Focus on accurate content changes only.

    Example diff format:
    --- lib/functions/example.py
    +++ lib/functions/example.py
     def some_function():
    -    print("Old line")
    +    print("New line")
     
    Process:
    1. Takes diff string and file path.
    2. Adds line numbers internally.
    3. Saves diff to .webwright directory.
    4. Applies diff to file.
    5. Logs changes in changelog.

    :param diff: Diff string with changes (no line numbers/headers).
    :param file_path: Path of file to modify.
    :return: Dict with success status and messages.
    """

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        if not diff.strip():
            return {"success": False, "message": "Empty diff provided"}
        
        if not os.path.isfile(file_path):
            return {"success": False, "message": f"File not found at path: {file_path}"}

        webwright_dir = os.path.expanduser('~/.webwright')
        diff_dir = os.path.join(webwright_dir, 'diffs')
        os.makedirs(diff_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        diff_filename = f"{os.path.basename(file_path).split('.')[0]}_{timestamp}_diff.txt"
        diff_file_path = os.path.join(diff_dir, diff_filename)

        # Read original file
        with open(file_path, "r", encoding='utf-8') as file:
            original_content = file.read()

        # Add accurate line numbers to the diff
        numbered_diff = add_line_numbers_to_diff(original_content, diff)

        # Save the numbered diff
        with open(diff_file_path, 'w', encoding='utf-8') as diff_file:
            diff_file.write(numbered_diff)

        # Apply the numbered diff
        try:
            patched_lines = apply_diff(original_content.splitlines(), numbered_diff.splitlines())
        except Exception as e:
            logger.error(f"Failed to apply diff: {str(e)}")
            return {"success": False, "message": f"Failed to apply diff: {str(e)}"}

        # Write patched contents
        with open(file_path, "w", encoding='utf-8') as file:
            file.writelines(line + '\n' for line in patched_lines)

        # Log the change
        changelog_path = os.path.join(webwright_dir, 'changelog.txt')
        with open(changelog_path, 'a', encoding='utf-8') as changelog_file:
            changelog_file.write(f"{timestamp}: Applied diff {diff_filename} to {file_path}\n")

        logger.info(f"Successfully applied diff to {file_path}")
        return {
            "success": True,
            "message": f"Successfully applied diff to {file_path} and saved as {diff_filename}",
            "diff_file": diff_filename
        }

    except Exception as e:
        logger.error(f"An error occurred while applying diff: {str(e)}")
        return {"success": False, "message": f"An error occurred while applying diff: {str(e)}"}

def apply_diff(original_lines: List[str], diff_lines: List[str]) -> List[str]:
    # Filter out lines that are not part of the unified diff format
    unified_diff = [line for line in diff_lines if line.startswith((' ', '+', '-', '@'))]
    
    # Generate the patched lines by using difflib.restore
    patched_lines = list(difflib.restore(unified_diff, 2))  # 2 for the newer version
    
    # If restore didn't produce any output, return the original lines
    if not patched_lines:
        return original_lines
    
    return patched_lines