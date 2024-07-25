import logging
import os
from lib.function_wrapper import function_info_decorator
from lib.util import calculate_file_hash, ensure_diff_dir_exists
from lib.config import Config
import google.generativeai as genai
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_file_with_fallback_encoding(file_path):
    """
    Read a file with utf-8-sig, falling back to other encodings.
    """
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read(), encoding
        except UnicodeDecodeError:
            pass
    logger.error(f"Unable to read {file_path}")
    return None, None

def generate_diff(old_content, new_content, file_path):
    """Generate a proper unified diff between old and new content."""
    import difflib
    diff = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=file_path,
        tofile=file_path,
        n=3,  # Context lines
        lineterm='\n'
    )
    return ''.join(diff)

@function_info_decorator
def reverse_code_diff_on_file(file_path: str) -> dict:
    """
    Reverts a previously applied code diff on a file using the Gemini AI for analysis and suggestion.

    This function finds the corresponding diff in the .webwright/diffs directory using the file's name and hash,
    and then applies this diff in reverse to the target file to undo the changes.

    :param file_path: The path to the file where the changes should be reversed.
    :type file_path: str
    :return: A dictionary indicating the result of the operation.
    :rtype: dict
    """

    config = Config()

    try:
        # Get Gemini API key
        gemini_api_key = config.get_gemini_api_key()
        if not gemini_api_key:
            logger.warning("Gemini API key not available. This tool requires a Gemini token.")
            return {"error": "Gemini API key not available"}

        # Calculate the current file hash
        file_hash = calculate_file_hash(file_path)
        if not file_hash:
            return {"error": "Failed to calculate file hash."}

        # Search for the corresponding diff files
        diff_dir = ensure_diff_dir_exists()
        file_name = os.path.basename(file_path)
        matching_diffs = []

        for diff in os.listdir(diff_dir):
            if diff.startswith(file_name):
                try:
                    _, timestamp, original_hash = diff[:-5].rsplit('_', 2)
                    if original_hash == file_hash:
                        matching_diffs.append((diff, timestamp))
                except ValueError:
                    continue

        if not matching_diffs:
            return {"error": f"No matching diff file for {file_path} found."}

        # Order by timestamp
        matching_diffs.sort(key=lambda x: x[1], reverse=True)
        
        # Use the most recent matching diff file
        diff_to_use = matching_diffs[0][0]
        diff_file_path = os.path.join(diff_dir, diff_to_use)

        # Read the diff file
        diff_content, diff_encoding = read_file_with_fallback_encoding(diff_file_path)
        if diff_content is None:
            return {"error": f"Failed to read the diff file: {diff_file_path}"}

        # Read the current file content
        current_content, current_encoding = read_file_with_fallback_encoding(file_path)
        if current_content is None:
            return {"error": f"Failed to read the current file: {file_path}"}

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Prepare the prompt for Gemini
        prompt = f"""Reverse the following diff and apply it to the provided file content:

Diff to reverse:
{diff_content}

Current file content:
{current_content}

Please provide the updated file content after reversing and applying the diff. Return only the updated content, without any additional code, functions, or explanations."""

        # Use Gemini to process the file content and reversed diff, and generate a response
        response = model.generate_content(prompt)
        
        # Extract the updated file content from the response
        reversed_content = response.text.strip()
        
        # Generate a new diff
        new_diff = generate_diff(current_content, reversed_content, file_path)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(reversed_content)

        # Store the new diff
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_hash = calculate_file_hash(file_path)
        new_diff_file_name = f"{file_name}_{timestamp}_{new_hash}.diff"
        new_diff_file_path = os.path.join(diff_dir, new_diff_file_name)
        
        with open(new_diff_file_path, 'w', encoding='utf-8') as f:
            f.write(new_diff)

        return {
            "status": "success",
            "message": f"Diff reversed and applied successfully. New diff stored at {new_diff_file_path}.",
            "reversed_content": reversed_content,
            "new_diff": new_diff,
            "new_diff_file_path": new_diff_file_path
        }
    
    except Exception as e:
        logger.exception("Error in reverse_code_diff_on_file")
        return {"error": f"Failed to reverse diff: {str(e)}"}