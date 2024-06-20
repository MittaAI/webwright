from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import os
import shutil

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

        # Copy the contents of the templates directory to the installation directory
        shutil.copytree(templates_dir, os.path.join(install_dir, 'templates'), dirs_exist_ok=True)

        # Download the INSTRUCTOR model
        subprocess.run(["python", "-m", "InstructorEmbedding", "hkunlp/instructor-xl"])

# Read the requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='webwright',
    version='0.1.0',
    packages=find_packages(),
    package_data={
        'webwright': ['templates/*'],
    },
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'webwright = webwright.main:entry_point'
        ]
    },
    cmdclass={
        'install': CustomInstallCommand,
    },
)