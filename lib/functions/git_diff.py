import subprocess
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def git_diff() -> dict:
    """
    Runs the 'git diff' command and captures the output.
    We can use this to write a git commit message, which would get written to the github repo.
    Shows the changes to all files changed in the repo.
    
    :return: A dictionary containing the success status and the diff output or error message.
    :rtype: dict
    """
    try:
        result = subprocess.run(['git', 'diff'], capture_output=True, text=True, check=True)
        return {
            'success': True,
            'diff_output': result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': str(e)
        }