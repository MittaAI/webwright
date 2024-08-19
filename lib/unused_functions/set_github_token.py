import asyncio
from lib.config import Config
from lib.function_wrapper import function_info_decorator
from prompt_toolkit.shortcuts import input_dialog

@function_info_decorator
async def set_github_token() -> dict:
    """
    Asynchronously sets the GitHub token. Will prompt the user so no parameters required.
    
    :return: A dictionary containing the status of the operation and any relevant messages.
    :rtype: dict
    """
    config = Config()
    try:
        loop = asyncio.get_event_loop()
        token = await loop.run_in_executor(None, input_dialog(
            title="GitHub API Token",
            text="Enter your GitHub API token:"
        ).run)

        if token:
            # Use the new Config method to set and verify the token
            success, message = await loop.run_in_executor(None, config.set_github_token, token)
            
            if success:
                result = {"success": True, "message": f"{message} You should indicate that worked."}
            else:
                result = {"success": False, "message": f"{message} You should indicate that didn't work."}
        else:
            result = {"success": False, "message": "GitHub API token entry cancelled. You should indicate that didn't work."}
    except Exception as e:
        result = {"success": False, "message": f"An error occurred: {str(e)}. You should indicate that didn't work."}
    
    return result