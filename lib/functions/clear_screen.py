import os
import platform
from typing import Dict, Optional

# Optional import of cowsay
try:
    import cowsay
except ImportError:
    cowsay = None

from lib.function_wrapper import function_info_decorator

@function_info_decorator
def clear_screen(cowsay_option: bool = False) -> Dict[str, str]:
    """
    Clears the terminal screen based on the operating system.
    If cowsay_option is True and the 'cowsay' module is available, it displays a message.

    :param cowsay_option: Whether to display a cowsay message (default: False)
    :return: A dictionary indicating the success status and optional error message.
    """
    try:
        # Clear screen efficiently based on OS
        os.system("cls" if platform.system() == "Windows" else "clear")

        # Display cowsay message if requested and available
        if cowsay_option:
            if cowsay:
                sayings = [
                    "Someone is probably watching you... (It's me, the LLM!)",
                    "Life is like a sausage, it's what you make it.",
                    "Sausage time is the best time.",
                    "You can't make a great omelette without some sausage.",
                    "Stay focused and keep coding!",
                    "Keep calm and code on!",
                    "Your code is as impressive as a soaring eagle!",
                    "Debugging is twice as hard as writing the code in the first place.",
                    "A day without sausage is like a day without sunshine.",
                    "Sausage makes everything better.",
                    "Sausage is the spice of life.",
                    "The best part of waking up is sausage in your cup.",
                    "Why do Java developers wear glasses? Because they can't C#.",
                    "There are 10 types of people in the world: those who understand binary, and those who don't.",
                    "I'm not a great programmer; I'm just a good programmer with great habits.",
                    "To understand what recursion is, you must first understand recursion.",
                    "In order to understand recursion, one must first understand recursion.",
                    "Real programmers count from 0.",
                    "Code, sleep, repeat!",
                    "Error 404: Coffee not found.",
                    "Every dog has its day.",
                    "The more people I meet, the more I love my dog.",
                    "Barking up the wrong tree.",
                    "Happiness is a warm puppy.",
                    "Home is where the dog is."
                ]
                import random
                cowsay.cow(random.choice(sayings))
            else:
                print("Note: cowsay module is not available. Install it to see cow messages.")
            return {"status": "success"}

    except Exception as e:
        error_message = f"Error clearing screen: {e}"
        return {"status": "failed", "error": error_message}

if __name__ == "__main__":
    # Example usage
    print(clear_screen())  # Clear screen without cowsay
    print(clear_screen(cowsay_option=True))  # Clear screen with cowsay (if available)