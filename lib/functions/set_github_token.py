import asyncio
from lib.util import set_config_value
from lib.function_wrapper import function_info_decorator

@function_info_decorator
async def set_github_token() -> dict:
    """
    Asynchronously sets the GitHub token.
    
    :return: A dictionary containing the status of the operation and any relevant messages.
    :rtype: dict
    """
    try:
        loop = asyncio.get_event_loop()
        token = await loop.run_in_executor(None, input, "Enter your GitHub Token: ")
        if token:
            await loop.run_in_executor(None, set_config_value, "config", "GITHUB_API_TOKEN", token)
            result = {"success": True, "message": "GitHub API token set successfully."}
        else:
            result = {"success": False, "message": "GitHub API token entry cancelled."}
    except Exception as e:
        result = {"success": False, "message": f"An error occurred: {str(e)}"}
    return result