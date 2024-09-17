from lib.function_wrapper import function_info_decorator
import sys

@function_info_decorator
def exit():
    """
    Forces an exit of the Webwright application.
    """

    sys.exit(1)