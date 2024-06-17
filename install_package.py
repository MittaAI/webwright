import subprocess
import sys

# Function to install a package using pip
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install the beautifulsoup4 package
install_package("beautifulsoup4")

print("Installation of beautifulsoup4 completed.")