from lib.function_wrapper import function_info_decorator
from lib.config import Config
import asyncio

@function_info_decorator
async def get_api_model_config(config_type: str, spinner=None) -> dict:
    """
    Configure, validate, and retrieve API settings for OpenAI or Anthropic. Will return the model we're talking to as well.

    Asked about what model you are, or your identity? Use this function!
    
    This function performs the following tasks based on the config_type:
    1. For 'switch_provider':
    - Allows switching between OpenAI and Anthropic as the preferred API
    - Validates the selected API's key and model, prompting for setup if needed
    2. For 'openai' or 'anthropic':
    - Validates existing API key or prompts for a new one
    - Sets the validated key in the configuration
    - Selects and sets an appropriate model for the API
    3. For 'set_openai_model' or 'set_anthropic_model':
    - Checks for a valid API key, prompting for one if not present
    - Allows selection of a specific model for the given API
    4. For 'get_config':
    - Retrieves and returns the current API configuration, including the preferred API, API key status, and selected model

    :param config_type: Specifies the configuration action. 
                        Options: 'switch_provider', 'openai', 'anthropic', 'set_openai_model', 'set_anthropic_model', 'get_config'
    :type config_type: str
    :param spinner: Optional progress indicator for long-running operations
    :type spinner: object

    :return: A dictionary with 'success' (bool) and 'message' (str) keys. 
             For 'get_config', also includes 'preferred_api', 'api_key_set', and 'model' keys.
    :rtype: dict

    :raises ValueError: If an invalid config_type is provided
    """
    config = Config()
    
    # Clear the cache for token validation functions
    config.check_openai_token.cache_clear()
    config.check_anthropic_token.cache_clear()
    
    try:
        loop = asyncio.get_event_loop()

        async def validate_and_set_key(api_type):
            existing_key = config.get_config_value("config", f"{api_type.upper()}_API_KEY")
            if existing_key and existing_key != "NONE":
                keep_existing = await loop.run_in_executor(None, input, f"An {api_type} API key is already set. Do you want to keep it? (y/n): ")
                if keep_existing.lower() == 'y':
                    is_valid = await loop.run_in_executor(None, getattr(config, f"check_{api_type}_token"), existing_key)
                    if is_valid:
                        return {"success": True, "message": f"Kept existing {api_type} API key."}
                    else:
                        print(f"Existing {api_type} API key is invalid. Please enter a new one.")
            
            token = await loop.run_in_executor(None, input, f"Enter your {api_type} API key: ")
            if token:
                is_valid = await loop.run_in_executor(None, getattr(config, f"check_{api_type}_token"), token)
                if is_valid:
                    config.set_config_value("config", f"{api_type.upper()}_API_KEY", token)
                    return {"success": True, "message": f"{api_type} API key set successfully."}
                else:
                    return {"success": False, "message": f"Invalid {api_type} API key. Please try again."}
            else:
                return {"success": False, "message": f"{api_type} API key entry cancelled."}

        async def set_model(api_type):
            if api_type == 'openai':
                new_model = await loop.run_in_executor(None, config.select_openai_model, config.get_openai_api_key())
            else:
                new_model = await loop.run_in_executor(None, config.select_anthropic_model)
            
            if new_model:
                config.set_config_value("config", f"{api_type.upper()}_MODEL", new_model)
                return {"success": True, "message": f"{api_type.capitalize()} model set to {new_model}."}
            else:
                return {"success": False, "message": f"{api_type.capitalize()} model selection cancelled or failed."}

        async def setup_api(api_type):
            key_result = await validate_and_set_key(api_type)
            if not key_result['success']:
                return key_result
            
            model_result = await set_model(api_type)
            if not model_result['success']:
                return model_result
            
            return {"success": True, "message": f"{api_type.capitalize()} API configured successfully."}

        if config_type == 'get_config':
            preferred_api = config.get_config_value("config", "PREFERRED_API")
            api_key = config.get_config_value("config", f"{preferred_api.upper()}_API_KEY") if preferred_api else None
            model = config.get_config_value("config", f"{preferred_api.upper()}_MODEL") if preferred_api else None
            return {
                "success": True,
                "message": f"Current configuration retrieved. Your model and provider are provided below. Allows you to respond to who you are.",
                "preferred_api": preferred_api,
                "api_key_set": bool(api_key and api_key != "NONE"),
                "model": model if model and model != "NONE" else None
            }
        
        if config_type == 'switch_provider':
            current_provider = config.get_config_value("config", "PREFERRED_API")
            print(f"Current preferred API: {current_provider}")
            new_provider = await loop.run_in_executor(None, input, "Enter the API to switch to (openai/anthropic): ")
            
            if new_provider.lower() not in ['openai', 'anthropic']:
                return {"success": False, "message": "Invalid provider. Must be 'openai' or 'anthropic'."}
            
            setup_result = await setup_api(new_provider.lower())
            if setup_result['success']:
                config.set_config_value("config", "PREFERRED_API", new_provider.lower())
                result = {"success": True, "message": f"Switched to {new_provider.capitalize()} as preferred API."}
            else:
                result = setup_result

        elif config_type in ['openai', 'anthropic']:
            result = await setup_api(config_type)

        elif config_type in ['set_openai_model', 'set_anthropic_model']:
            api_type = 'openai' if config_type == 'set_openai_model' else 'anthropic'
            api_key = config.get_openai_api_key() if api_type == 'openai' else config.get_anthropic_api_key()
            
            if not api_key or api_key == "NONE":
                key_result = await validate_and_set_key(api_type)
                if not key_result['success']:
                    return key_result
            
            result = await set_model(api_type)

        else:
            raise ValueError(f"Invalid config_type: {config_type}. Must be 'switch_provider', 'openai', 'anthropic', 'set_openai_model', or 'set_anthropic_model'.")

    except Exception as e:
        result = {"success": False, "message": f"An error occurred: {str(e)}"}

    return result