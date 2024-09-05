from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import os
import shutil
from pathlib import Path

class CustomInstallCommand(install):
    def run(self):
        # Run the regular installation
        install.run(self)

        # Get the package directory
        package_dir = os.path.dirname(os.path.abspath(__file__))

        # Path to the templates directory
        templates_dir = os.path.join(package_dir, 'templates')

        # Path to the installation directory
        install_dir = os.path.join(self.install_lib, 'webwright')

        # Download the INSTRUCTOR model
        subprocess.run(["python", "-m", "InstructorEmbedding", "hkunlp/instructor-xl"])

# Read the requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the README file with UTF-8 encoding
this_directory = Path(__file__).parent
try:
    with open(this_directory / "README.md", encoding="utf-8") as f:
        long_description = f.read()
except Exception as e:
    print(f"An error occurred while reading README.md: {e}")
    long_description = ""

setup(
    name='webwright',
    version='0.0.4',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'webwright = webwright.main:entry_point'
        ]
    },
    cmdclass={
        'install': CustomInstallCommand,
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
)