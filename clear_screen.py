import os
import platform

def clear_screen():
    current_os = platform.system()
    if current_os == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

if __name__ == "__main__":
    clear_screen()
