import logging
import google.generativeai as genai
from lib.function_wrapper import function_info_decorator
from lib.util import store_diff
import difflib
from lib.config import Config

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_code_from_markdown(content):
    """
    Extract code from markdown-style code blocks, including the language type if specified.
    
    :param content: The markdown content containing code blocks.
    :return: A tuple containing the extracted code and the language type (if specified).
    """
    lines = content.split('\n')
    in_code_block = False
    code_lines = []
    language = None
    
    for line in lines:
        if line.startswith('```'):
            if not in_code_block:
                # Check for language specification
                lang_spec = line[3:].strip()
                if lang_spec:
                    language = lang_spec
            in_code_block = not in_code_block
            continue
        if in_code_block:
            code_lines.append(line)
    
    extracted_code = '\n'.join(code_lines) if code_lines else content
    return extracted_code, language

def generate_diff(old_content, new_content, file_path):
    """Generate a proper unified diff between old and new content."""
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
def apply_code_diff_to_file(diff: str, update_query: str, file_path: str, override_length_limit: bool = False) -> dict:
    """
    Applies a code pseudo diff to a file using Gemini AI for analysis and suggestion.
    
    This function should only be called with a pseudo diff of the changes to be applied to the file.
    
    An internal function will update the file with the proper changes and store the new functional diff.
    
    :param diff: The code pseudo diff to be applied, with + or - on front of lines changes. 
                 This should be a string representation of the changes, typically in a format similar to the output of 'git diff'. This strictly does not need to be perfect but should include all changes required. The calling LLM should always use + for new lines and - for line deletions.
                 If the diff is not in the correct format, this function will return an error.
    :type diff: str
    :param update_query: The original query from the user requesting the file modification.
    :type update_query: str
    :param file_path: The path to the file where the changes should be applied.
    :type file_path: str
    :param override_length_limit: A flag to override the length limit check. Default is False.
    :type override_length_limit: bool
    :return: A dictionary containing the result of the operation. It includes:
             - 'status': 'success' if the operation was successful, otherwise not present.
             - 'message': A description of the action taken.
             - 'suggested_changes': The improvements suggested and applied by the AI.
             - 'new_diff': The generated diff between the original and updated content.
             - 'error': Description of the error if the operation failed.
    :rtype: dict
    
    :raises Exception: If there's an error in reading the file, processing with the 
                       Gemini API, or applying changes to the file.
    
    Note: This function requires a valid Gemini API key to be available through 
    the get_gemini_api_key() function. If the API key is not available, the function 
    will return an error message.
    """
    config = Config()

    try:
        # Get Gemini API key
        gemini_api_key = config.get_gemini_api_key()
        if not gemini_api_key:
            logger.warning("Gemini API key not available. Some functionality may be limited.")
            return {"error": "Gemini API key not available"}

        # Check if the diff contains + or - in the first space of any line
        if not any(line.strip().startswith(('+', '-')) for line in diff.split('\n')):
            return {"error": "Invalid diff format. The diff must contain lines starting with + or -."}

        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            original_content = file.read()

        # Check if the diff is within 90% of the original file content length, unless override_length_limit is True
        if not override_length_limit and len(original_content) > 1024 and len(diff) > len(original_content) * 0.90:
            return {"error": "Diff size is too large compared to the original file content. As the LLM isn't paying attention to the tool use, we'll remind it that it needs to use + or - in front of the changes, and not give us code blocks that aren't changes (other than reference to changes). If you want to override this limit, set override_length_limit to True."}

        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Prepare the prompt for Gemini
        prompt = f"""Look at the provided change request, pseudo diff, and the source code being modified, then apply the pseudo diff to the file to produce a complete file:

The user request's to modify the file:
{update_query}

The resulting pseudo diff to apply to satisfy the user request:
{diff}

File Content:
{original_content}

Please provide the updated file content after applying the pseudo diff. Return only the updated content, without any additional code, functions, or explanations."""

        # Use Gemini to process the file content and diff, and generate a response
        response = model.generate_content(prompt)
        
        # Extract the updated file content from the response and remove code blocks if present
        updated_content, language = extract_code_from_markdown(response.text.strip())
        
        # Generate a new diff
        new_diff = generate_diff(original_content, updated_content, file_path)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

        # Store the new diff (done after updating the file)
        diff_file_path = store_diff(new_diff, file_path)

        return {
            "status": "success",
            "message": f"Diff applied, changes made to the file, and new diff stored at {diff_file_path}.",
            "suggested_changes": updated_content,
            "new_diff": new_diff,
            "diff_file_path": diff_file_path,
            "language": language
        }
    except Exception as e:
        logger.error(f"Error in apply_code_diff_to_file: {str(e)}")
        return {"error": f"Failed to apply diff: {str(e)}"}