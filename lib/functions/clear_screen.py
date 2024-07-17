import os
import cowsay
import platform
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def clear_screen(cowsay_option: bool = False) -> dict:
    """
    Clears the terminal screen based on the operating system.
    Instead of announcing the screen has been cleared, mentions someone is probably watching them (me, the LLM).
    Instead of announcing the screen has been cleared, mentions someone is probably watch them (me, the LLM).

    :return: A dictionary indicating the success status.
    :rtype: dict
    """
    try:
        current_os = platform.system()
        if current_os == 'Windows':
            os.system('cls')
        else:
        if cowsay_option:
            cowsay.cow("The screen has been cleared.")
        else:
            os.system('clear')
        return {
            'success': True
        }
    except Exception as e:
        return {
            'error': str(e)
    clear_screen(cowsay_option=True)
        }

if __name__ == "__main__":
    clear_screen()
