from lib.function_wrapper import function_info_decorator
from lib.util import set_config_value, get_config_value, check_openai_token, check_anthropic_token

@function_info_decorator
def set_api_config(config_type: str, value: str) -> dict:
    """
    Sets the API configuration for OpenAI or Anthropic, or sets the API to use for function calls.
    
    :param config_type: The type of configuration to set. Can be 'openai_key', 'anthropic_key', or 'preferred_api'.
    :type config_type: str
    :param value: The value to set for the chosen configuration type.
    :type value: str
    :return: A dictionary containing the status of the operation and any relevant messages.
    :rtype: dict
    """
    try:
        if config_type == 'openai_key':
            if check_openai_token(value):
                set_config_value("config", "OPENAI_API_KEY", value)
                return {"success": True, "message": "OpenAI API key set successfully."}
            else:
                return {"success": False, "message": "Invalid OpenAI API key."}
        
        elif config_type == 'anthropic_key':
            if check_anthropic_token(value):
                set_config_value("config", "ANTHROPIC_API_KEY", value)
                return {"success": True, "message": "Anthropic API key set successfully."}
            else:
                return {"success": False, "message": "Invalid Anthropic API key."}
        
        elif config_type == 'preferred_api':
            allowed_apis = ['openai', 'anthropic']
            if value.lower() in allowed_apis:
                set_config_value("config", "PREFERRED_API", value.lower())
                return {"success": True, "message": f"Preferred API set to {value.lower()}."}
            else:
                return {"success": False, "message": f"Invalid API choice. Allowed options are: {', '.join(allowed_apis)}"}
        
        else:
            return {"success": False, "message": "Invalid config_type. Must be 'openai_key', 'anthropic_key', or 'preferred_api'."}

    except Exception as e:
        return {"success": False, "message": f"An error occurred: {str(e)}"}

@function_info_decorator
def get_current_api_config() -> dict:
    """
    Retrieves the current API configuration.
    
    :return: A dictionary containing the current API configuration.
    :rtype: dict
    """
    try:
        openai_key = get_config_value("config", "OPENAI_API_KEY")
        anthropic_key = get_config_value("config", "ANTHROPIC_API_KEY")
        preferred_api = get_config_value("config", "PREFERRED_API")
        
        return {
            "success": True,
            "openai_key_set": bool(openai_key),
            "anthropic_key_set": bool(anthropic_key),
            "preferred_api": preferred_api or "Not set"
        }
    except Exception as e:
        return {"success": False, "message": f"An error occurred: {str(e)}"}