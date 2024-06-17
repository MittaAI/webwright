import subprocess
import sys
import logging
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def install_package(package: str) -> dict:
    """
    Installs a Python package using pip.

    :param package: The name of the package to install.
    :type package: str

    :return: A dictionary indicating the success or failure of the installation.
    :rtype: dict
    """
    try:
        # Install the package using pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # Log the successful installation
        logging.info(f"Installation of {package} completed.")
        
        return {
            "success": True,
            "message": f"Installation of {package} completed successfully."
        }
    except subprocess.CalledProcessError as e:
        # Log the installation failure
        logging.error(f"Installation of {package} failed.")
        logging.error(f"Error: {str(e)}")
        
        return {
            "success": False,
            "error": f"Installation of {package} failed.",
            "reason": str(e)
        }