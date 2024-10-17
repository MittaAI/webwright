from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
from pathlib import Path

class CustomInstallCommand(install):
    def run(self):
        install.run(self)
        subprocess.check_call([
            "pip", "install", "--no-deps", "--force-reinstall", 
            "chroma-hnswlib==0.7.3"
        ])

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

requirements = [req for req in requirements if not req.startswith('chroma-hnswlib')]

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name='webwright',
    version='0.0.5',
    author='Kord Campbell',
    author_email='kordless@gmail.com',
    description="Webwright: The Ghost in Your Shell 👻💻",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MittaAI/webwright",
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
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    keywords="ai terminal shell automation development tools",
)