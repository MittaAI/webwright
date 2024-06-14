from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess

class CustomInstallCommand(install):
    def run(self):
        # Run the regular installation
        install.run(self)

        # Download the INSTRUCTOR model
        subprocess.run(["python", "-m", "InstructorEmbedding", "hkunlp/instructor-xl"])

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
            'webwright = webwright.main:entry_point'
        ]
    },
    cmdclass={
        'install': CustomInstallCommand,
    },
)