import os
import difflib
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TODO
"""
Where do I save the diff file?
Should we havea  diff log?
"""

diff_path = "/Users/andylegrand/Desktop/untitled folder/diff.txt"
new_file_path = "/Users/andylegrand/Desktop/untitled folder/new_file.py"

from lib.function_wrapper import function_info_decorator
@function_info_decorator
def create_code_diff_and_apply(diff: str, file_path: str, block_delimiter: str = "") -> dict:
    """
    Applies a diff to a file and logs changes.

    The diff should include line numbers and use '-' for removed lines, 
    and '+' for added lines. This function will apply these changes to 
    the original file, which doesn't have line numbers.

    Example Diff to replcae line 25 with 4 new lines, delete line 56 and insert a new line at line 70:
    -|00025|\t    with open(file_path, 'r') as file:
    +|00025|\t    with open(file_path, 'r', encoding='utf-8') as file:
    +|00025|\t        import logging
    +|00025|\t        logging.basicConfig(level=logging.INFO)
    +|00025|\t        logging.info(f'Reading file: {file_path}')
    -|00056|\tprint("Yeet")
    +|00070|\tprint("Hello, World!")

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

        # write diff to file
        with open(diff_path, 'w', encoding='utf-8') as file:
            file.write(diff)

        # Read the original file
        with open(file_path, 'r', encoding='utf-8') as file:
            original_lines = file.readlines()

        # Apply the diff
        modified_lines = original_lines[:]
        chunks = diff.split(block_delimiter) if block_delimiter else [diff]
        for chunk in chunks:
            operations = parse_diff(chunk)
            prev_op = None

            # Messes up spacing
            for op in reversed(operations):
                line_number = op['line']
                # Check if the line number is in ascending order
                if prev_op and line_number > prev_op['line']:
                    return {"success": False, "message": "Line numbers must be in ascending order"}
                # check that deletions are done before additions on the same line
                if prev_op and prev_op['line'] == line_number and prev_op['type'] == 'remove' and op['type'] == 'add':
                    return {"success": False, "message": "Line deletions must be done before additions on the same line"}
                if op['type'] == 'add':
                    modified_lines.insert(line_number, op['content'])
                elif op['type'] == 'remove':
                    del modified_lines[line_number - 1]
                prev_op = op

                # FOR TESTING
                with open(new_file_path, 'w', encoding='utf-8') as file:
                    file.writelines(modified_lines)

            # Write the modified content back to the file
            #with open(file_path, 'w', encoding='utf-8') as file:
            with open(new_file_path, 'w', encoding='utf-8') as file:
                file.writelines(modified_lines)

            return {"success": True, "message": "Diff applied successfully"}
    except Exception as e:
        logger.error(f"Error applying diff: {e}")
        return {"success": False, "message": f"Error applying diff: {e}"}

def parse_diff(diff: str) -> list:
    operations = []
    for line in diff.splitlines():
        if line.startswith('+'):
            operations.append({'type': 'add', 'line': int(line[2:7].strip()), 'content': line[8:] + '\n'})
        elif line.startswith('-'):
            operations.append({'type': 'remove', 'line': int(line[2:7].strip())})
    return operations

"""
if __name__ == "__main__":
    # Create a sample file for testing
    sample_file_path = "/Users/andylegrand/Desktop/untitled folder/sample_file.txt"
    original_content = [
        "line 1\n",
        "line 2\n",
        "line 3\n",
        "line 4\n",
        "line 5\n",
        "line 6\n",
        "line 7\n",
        "line 8\n",
        "line 9\n",
        "line 10\n"
    ]

    def reset_sample_file():
        with open(sample_file_path, 'w', encoding='utf-8') as file:
            file.writelines(original_content)

    def assert_file_content(expected_content):
        with open(sample_file_path, 'r', encoding='utf-8') as file:
            modified_content = file.readlines()
        assert modified_content == expected_content

    # Try deleting lines 2 and 6-8
    reset_sample_file()
    diff = (
        "-|00002|\tline 2\n"
        "-|00006|\tline 6\n"
        "-|00007|\tline 7\n"
        "-|00008|\tline 8\n"
    )
    expected_content = [
        "line 1\n",
        "line 3\n",
        "line 4\n",
        "line 5\n",
        "line 9\n",
        "line 10\n"
    ]
    result = create_code_diff_and_apply(diff, sample_file_path)
    assert result['success']
    assert_file_content(expected_content)

    # Try adding a line after line 2 and 3 lines after line 6
    reset_sample_file()
    diff = (
        "+|00002|\tinserted line 1\n"
        "+|00006|\tinserted line 2\n"
        "+|00006|\tinserted line 3\n"
        "+|00006|\tinserted line 4\n"
    )
    expected_content = [
        "line 1\n",
        "line 2\n",
        "inserted line 1\n",
        "line 3\n",
        "line 4\n",
        "line 5\n",
        "line 6\n",
        "inserted line 2\n",
        "inserted line 3\n",
        "inserted line 4\n",
        "line 7\n",
        "line 8\n",
        "line 9\n",
        "line 10\n"
    ]
    result = create_code_diff_and_apply(diff, sample_file_path)
    assert result['success']
    assert_file_content(expected_content)

    # Replace line 2 with 3 new lines, delete line 6, and add 2 lines after line 8
    reset_sample_file()
    diff = (
        "-|00002|\tline 2\n"
        "+|00002|\tinserted line 1\n"
        "+|00002|\tinserted line 2\n"
        "+|00002|\tinserted line 3\n"
        "-|00006|\tline 6\n"
        "+|00008|\tinserted line 1\n"
        "+|00008|\tinserted line 2\n"
    )
    expected_content = [
        "line 1\n",
        "inserted line 1\n",
        "inserted line 2\n",
        "inserted line 3\n",
        "line 3\n",
        "line 4\n",
        "line 5\n",
        "line 7\n",
        "line 8\n",
        "inserted line 1\n",
        "inserted line 2\n",
        "line 9\n",
        "line 10\n"
    ]
    result = create_code_diff_and_apply(diff, sample_file_path)
    assert_file_content(expected_content)

    # Try an invalid diff where line numbers are not in ascending order
    reset_sample_file()
    diff = (
        "-|00002|\tline 2\n"
        "-|00001|\tline 1\n"
    )
    result = create_code_diff_and_apply(diff, sample_file_path)
    assert not result['success'] and "Line numbers must be in ascending order" in result['message']

    # Try an invalid diff where line deletions are done after additions on the same line
    reset_sample_file()
    diff = (
        "+|00002|\tinserted line 1\n"
        "-|00002|\tline 2\n"
    )
    result = create_code_diff_and_apply(diff, sample_file_path)
    assert not result['success'] and "Line deletions must be done before additions on the same line" in result['message']

"""

if __name__ == "__main__":
    # Create a sample file for testing
    sample_file_path = "/Users/andylegrand/Desktop/untitled folder/bank_script.py"

    # read diff from file
    with open(diff_path, 'r', encoding='utf-8') as file:
        diff = file.read()

    # apply diff to file
    result = create_code_diff_and_apply(diff, sample_file_path)
    print(result)
