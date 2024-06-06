import os
import string
import random
import configparser
from coolname import generate_slug

def random_string(size=6, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# Read the .webwright_config file
config = configparser.ConfigParser()
config.read(".webwright_config")

# Get the username
username_key = "username"

def set_username(username):
    config.set("auth", username_key, username)
    with open(".webwright_config", "w") as configfile:
        config.write(configfile)
    return username

def get_username():
    if config.has_option("auth", username_key):
        username = config.get("auth", username_key)
        print(f"system> You are logged in as `{username}`.")
        return username
    else:
        username = generate_slug(2)
        return set_username(username)