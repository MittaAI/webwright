import os
import platform
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def clear_screen() -> dict:
    """
    Clears the terminal screen based on the operating system.

    Instead of announcing the screen has been cleared, mentions someone is probably watch them (me, the LLM).

    :return: A dictionary indicating the success status.
    :rtype: dict
    """
    try:
        current_os = platform.system()
        if current_os == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
        return {
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    clear_screen()
