import os
import string
import random
import shutil
from configparser import ConfigParser
from coolname import generate_slug

def random_string(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# Read the .webwright_config file
config_file = ".webwright_config"
config = ConfigParser()

def read_config():
    config.read(config_file)

def write_config():
    with open(config_file, "w") as f:
        config.write(f)

def set_username(username):
    if not config.has_section("config"):
        config.add_section("config")
    config.set("config", "username", username)
    write_config()
    return username

def get_username():
    if config.has_option("config", "username"):
        username = config.get("config", "username")
        print(f"system> You are logged in as `{username}`.")
        return username
    else:
        username = generate_slug(2)
        return set_username(username)

def get_config_value(key):
    if config.has_option("config", key):
        return config.get("config", key)
    else:
        return None

def setup_ssh_key():
    ssh_directory = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_directory):
        print("system> No SSH keys found.")
        return
    keys = [file for file in os.listdir(ssh_directory) if os.path.isfile(os.path.join(ssh_directory, file)) and not file.endswith(".pub")]
    if not keys:
        print("system> No SSH keys found.")
        return
    print("system> Available SSH keys:")
    for i, key in enumerate(keys, start=1):
        print(f"{i}. {key}")
    while True:
        try:
            choice = int(input("system> Enter the number of the SSH key to use: "))
            if 1 <= choice <= len(keys):
                selected_key = keys[choice - 1]
                break
            else:
                print("system> Invalid choice. Please try again.")
        except ValueError:
            print("system> Invalid input. Please enter a valid number.")
    ssh_key_path = os.path.join(ssh_directory, selected_key)
    webwright_dir = os.path.expanduser("~/.webwright")
    os.makedirs(webwright_dir, exist_ok=True)
    destination_path = os.path.join(webwright_dir, "id_rsa")
    shutil.copy2(ssh_key_path, destination_path)
    print(f"system> SSH key '{selected_key}' has been set up and saved in '{destination_path}'.")

def set_anthropic_api_key(api_key):
    if not config.has_section("config"):
        config.add_section("config")
    config.set("config", "anthropic_key", api_key)
    write_config()

def get_anthropic_api_key():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        anthropic_key = get_config_value("anthropic_key")
    return anthropic_key

# Initialize configuration
read_config()