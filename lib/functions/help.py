# lib/functions/help.py
from lib.function_wrapper import function_info_decorator, tools

@function_info_decorator
def help() -> dict:
    """
    Provides help information about the available functions.
    When the help function is used, the output should be reconstructed for the user such that each method presents as a command.
    Commands (functions) are run from the command line interface. The LLM will interpret these and add the calling parameters, if needed.
    And example would be "help", which provides help and information on commands, a list or details.
    :return: A dictionary containing the help information.
    :rtype: dict
    """
    help_info = []
    for tool in tools:
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
