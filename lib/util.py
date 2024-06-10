import os
import string
import random
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

# Initialize configuration
read_config()

# Example usage
get_username()
