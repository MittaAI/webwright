# lib/functions/chat.py
import logging
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def chat(assistant_response: str) -> dict:
    """
    Returns a dictionary containing the assistant's response.
    :param assistant_response: The assistant's response message.
    :type assistant_response: str
    :return: A dictionary containing the assistant's response.
    :rtype: dict
    """
    logging.info("in chat")
    return {
        "success": True,
        "response": assistant_response
    }
