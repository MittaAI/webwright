from setuptools import setup, find_packages

# Read the requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='webwright',
    version='0.1.0',
    packages=find_packages(),
    install_requires=requirements,
	entry_points={
	    'console_scripts': [
	        'webwright = webwright:entry_point'
	    ]
	},
)