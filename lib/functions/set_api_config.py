from lib.function_wrapper import function_info_decorator
from lib.util import set_config_value, check_openai_token, check_anthropic_token
import asyncio
import json

@function_info_decorator
async def set_api_config_dialog(config_type: str, spinner=None) -> dict:
    """
    Asynchronously set the API configuration for OpenAI or Anthropic, or set the preferred API to use for function calls.
    
    :param config_type: The type of configuration to set. Can be 'openai_key', 'anthropic_key', or 'preferred_api'.
    :type config_type: str
    :param spinner: Optional spinner object to handle UI feedback.
    :type spinner: object
    :return: A dictionary containing the status of the operation and any relevant messages.
    :rtype: dict
    """
    try:
        if spinner:
            spinner.stop()

        loop = asyncio.get_event_loop()

        if config_type == 'openai_key':
            token = await loop.run_in_executor(None, input, "Enter your OpenAI API key: ")
            if token:
                is_valid = await loop.run_in_executor(None, check_openai_token, token)
                if is_valid:
                    await loop.run_in_executor(None, set_config_value, "config", "OPENAI_API_KEY", token)
                    result = {"success": True, "message": "OpenAI API key set successfully."}
                else:
                    result = {"success": False, "message": "Invalid OpenAI API key. Please try again."}
            else:
                result = {"success": False, "message": "OpenAI API key entry cancelled."}
        
        elif config_type == 'anthropic_key':
            token = await loop.run_in_executor(None, input, "Enter your Anthropic API key: ")
            if token:
                is_valid = await loop.run_in_executor(None, check_anthropic_token, token)
                if is_valid:
                    await loop.run_in_executor(None, set_config_value, "config", "ANTHROPIC_API_KEY", token)
                    result = {"success": True, "message": "Anthropic API key set successfully."}
                else:
                    result = {"success": False, "message": "Invalid Anthropic API key. Please try again."}
            else:
                result = {"success": False, "message": "Anthropic API key entry cancelled."}
        
        elif config_type == 'preferred_api':
            await loop.run_in_executor(None, print, "Select the preferred API to use:")
            await loop.run_in_executor(None, print, "1. OpenAI")
            await loop.run_in_executor(None, print, "2. Anthropic")
            choice = await loop.run_in_executor(None, input, "Enter your choice (1 or 2): ")
            if choice == '1':
                await loop.run_in_executor(None, set_config_value, "config", "PREFERRED_API", "openai")
                result = {"success": True, "message": "Preferred API set to OpenAI."}
            elif choice == '2':
                await loop.run_in_executor(None, set_config_value, "config", "PREFERRED_API", "anthropic")
                result = {"success": True, "message": "Preferred API set to Anthropic."}
            else:
                result = {"success": False, "message": "Invalid choice. Preferred API selection cancelled."}
        
        else:
            result = {"success": False, "message": "Invalid config_type. Must be 'openai_key', 'anthropic_key', or 'preferred_api'."}

    except Exception as e:
        result = {"success": False, "message": f"An error occurred: {str(e)}"}

    finally:
        if spinner:
            spinner.start()

    return result