import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def cat_file(file_path: str, add_line_numbers: bool = False) -> dict:
    """
    Reads the contents of a file and returns them as a string, optionally with line numbers.
    
    :param file_path: The path of the file to read.
    :type file_path: str
    :param add_line_numbers: Whether to add line numbers to the output.
    :type add_line_numbers: bool
    
    :return: A dictionary containing the success status and the file contents or an error message.
    :rtype: dict
    """
    if not isinstance(file_path, str):
        return {
            "success": False,
            "error": "Invalid input",
            "reason": f"Expected a string for file_path, got {type(file_path).__name__}"
        }
    
    if not file_path:
        return {
            "success": False,
            "error": "Invalid input",
            "reason": "File path cannot be empty"
        }

    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": "File not found",
                "reason": f"The file '{file_path}' does not exist."
            }
        
        # Read the contents of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            contents = file.readlines()
        
        if add_line_numbers:
            # Add line numbers to the contents
            numbered_contents = "# This file has been augmented with line numbers for reference\n" \
                                "# Format: =|00001|original line\n" \
                                "# When you are building a diff from this, a + on the front indicates an addition at that line number\n" \
                                "# When you are building a diff from this, a - on the front indicates a deletion at that line number\n" \
                                "".join(
                                    f"=|{str(line_number).zfill(5)}|\t{line}"
                                    for line_number, line in enumerate(contents, start=1)
                                )
            return {
                "success": True,
                "contents": numbered_contents
            }
        else:
            return {
                "success": True,
                "contents": "".join(contents)
            }
    except PermissionError:
        return {
            "success": False,
            "error": "Permission denied",
            "reason": f"You do not have permission to read the file '{file_path}'."
        }
    except Exception as e:
        return {
            "success": False,
            "error": "File reading failed",
            "reason": str(e)
        }

if __name__ == "__main__":
    file_path = "/Users/andylegrand/Desktop/Summer24/webwright/lib/functions/search_file.py"
    result = cat_file(file_path, add_line_numbers=True)
    
    # write to file
    with open("output.txt", "w") as file:
        file.write(result["contents"])