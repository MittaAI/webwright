import os
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def cat_file(file_path: str) -> dict:
    """
    Reads the contents of a file and returns them as a string with line numbers.
    
    :param file_path: The path of the file to read.
    :type file_path: str
    
    :return: A dictionary containing the success status and the file contents or an error message.
    :rtype: dict
    """
    try:
        # Check if the file exists
        if not os.path.isfile(file_path):
            return {
                "success": False,
                "error": "File not found",
                "reason": f"The file '{file_path}' does not exist."
            }
        
        # Read the contents of the file
        with open(file_path, 'r') as file:
            contents = file.readlines()
        
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
    result = cat_file(file_path)
    
    # write to file
    with open("output.txt", "w") as file:
        file.write(result["contents"])
