import os
import string
import random

from coolname import generate_slug

def random_string(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# Read the .webwright_config file
config_file = ".webwright_config"
config = {}

def read_config():
    with open(config_file, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                config[key] = value

def write_config():
    with open(config_file, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")

def set_username(username):
    config["username"] = username
    write_config()
    return username

def get_username():
    if "username" in config:
        username = config["username"]
        print(f"system> You are logged in as `{username}`.")
        return username
    else:
        username = generate_slug(2)
        return set_username(username)

# Initialize configuration
read_config()

# Example usage
get_username()
