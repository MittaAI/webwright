import os
import difflib
import logging
from lib.function_wrapper import function_info_decorator

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@function_info_decorator
def create_code_diff_and_apply(diff: str, file_path: str, block_delimiter: str = "") -> dict:
    """
    Applies a diff to a file and logs changes.

    The diff should include line numbers and use '-' for removed lines, 
    and '+' for added lines. This function will apply these changes to 
    the original file, which doesn't have line numbers.

    Example Diff:
    -|00025|        with open(file_path, 'r') as file:
    +|00025|        with open(file_path, 'r', encoding='utf-8') as file:
    +|00026|            import logging
    +|00026|            logging.basicConfig(level=logging.INFO)
    +|00026|            logging.info(f'Reading file: {file_path}')
    -|00056|    with open("output.txt", "w") as file:
    +|00056|    with open("output.txt", "w", encoding='utf-8') as file:

    :param diff: Diff string with changes.
    :param file_path: Path of file to modify.
    :param block_delimiter: Optional delimiter for multiple change blocks.
    :return: Dict with success status and messages.
    """
    try:
        if not diff.strip():
            return {"success": False, "message": "Empty diff provided"}
        
        if not os.path.isfile(file_path):
            return {"success": False, "message": f"File not found at path: {file_path}"}

        # Read the original file
        with open(file_path, 'r', encoding='utf-8') as file:
            original_lines = file.readlines()

        # Apply the diff
        modified_lines = apply_diff(original_lines, diff, block_delimiter)
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(modified_lines)
        
        return {"success": True, "message": "Diff applied successfully"}
    except Exception as e:
        logger.exception("Failed to apply diff")
        return {"success": False, "message": str(e)}

def apply_diff(original_lines: list, diff: str, block_delimiter: str) -> list:
    modified_lines = original_lines[:]
    chunks = diff.split(block_delimiter) if block_delimiter else [diff]
    
    for chunk in chunks:
        operations = parse_diff(chunk)
        line_offset = 0
        for op in operations:
            line_number = op['line'] + line_offset
            if op['type'] == 'add':
                modified_lines.insert(line_number, op['content'])
                line_offset += 1
            elif op['type'] == 'remove':
                del modified_lines[line_number]
                line_offset -= 1
    
    return modified_lines

def parse_diff(diff: str) -> list:
    operations = []
    for line in diff.splitlines():
        if line.startswith('+'):
            operations.append({'type': 'add', 'line': int(line[2:7].strip()) - 1, 'content': line[8:] + '\n'})
        elif line.startswith('-'):
            operations.append({'type': 'remove', 'line': int(line[2:7].strip()) - 1})
    return operations

if __name__ == "__main__":
    file_path = "/path/to/your/file.txt"
    diff = """
-|00025|	        with open(file_path, 'r') as file:
+|00025|	        with open(file_path, 'r', encoding='utf-8') as file:
+|00026|	            import logging
+|00026|	            logging.basicConfig(level=logging.INFO)
+|00026|	            logging.info(f'Reading file: {file_path}')
-|00056|	    with open("output.txt", "w") as file:
+|00056|	    with open("output.txt", "w", encoding='utf-8') as file:
    """
    result = create_code_diff_and_apply(diff, file_path)
    print(result)

# TODO
"""
Change to work from the bottom up.
If there are two pluses (+) in a row, and the line numbers are sequential then return an error that explains they should be the same line number.
"""