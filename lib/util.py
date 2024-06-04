import os
import string
import random
from coolname import generate_slug

def random_string(size=6, chars=string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

# super basic authentication
auth_filename = ".auth"
username_key = "username="

def set_username(username):
	with open(auth_filename, "w") as file:
		file.write(f"{username_key}{username}\n")
	return username

def get_username():
	if os.path.exists(auth_filename):
		with open(auth_filename, "r") as file:
			content = file.readlines()
			username_found = False
			for line in content:
				if line.startswith(username_key):
					username = line[len(username_key):].strip()
					username_found = True
					print(f"system> You are logged in as `{username}`.")
					return username
			if not username_found:
				username = generate_slug(2)
	else:
		username = generate_slug(2)

	return set_username(username)