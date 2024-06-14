# lib/functions/help.py
from lib.function_wrapper import function_info_decorator, tools

@function_info_decorator
def help() -> dict:
    """
    Provides help information about the available functions.
    :return: A dictionary containing the help information.
    :rtype: dict
    """
    help_info = []
    for tool in tools:
        if tool['function']['name'] != 'i_have_failed_my_purpose':
            function_name = tool['function']['name']
            function_description = tool['function']['description']
            parameters = tool['function']['parameters']['properties']
            usage = f"{function_name}("
            for param, details in parameters.items():
                param_type = details['type']
                usage += f"{param}: {param_type}, "
            usage = usage.rstrip(", ") + ")"
            help_info.append({
                "name": function_name,
                "description": function_description,
                "usage": usage
            })
    return {
        "success": True,
        "functions": help_info
    }
