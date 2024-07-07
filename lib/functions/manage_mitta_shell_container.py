import os
import subprocess
import shutil
import pkg_resources
from lib.util import setup_logging, get_logger
from lib.function_wrapper import function_info_decorator

# Initialize logging
logger = setup_logging()

# This decorator registers the function into a wider package
@function_info_decorator
def manage_mitta_shell_container(action: str) -> dict:
    """
    Allows the local Mitta agent to manage a Docker container for a development web shell and containers for applications the shell and the user build, allowing the agent to start, stop, restart, and recreate container actions.
    
    Example: "start the shell" would start the shell container if it wasn't running.

    :param action: The action to perform: 'start', 'stop', 'restart', or 'recreate'.
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    # Generate a unique container name
    container_name = "mitta_shell"
    image_name = "mitta_shell"
    port_mapping = "7000:7000"
    
    # Paths
    current_dir = os.getcwd()
    log_directory = os.path.expanduser('~/.webwright/logs')
    log_file = os.path.join(log_directory, 'shell.log')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    temp_dir = os.path.join(current_dir, 'mitta_shell_temp')

    try:
        # Get the path to the installed templates directory
        template_dir = pkg_resources.resource_filename('webwright', 'templates/shell')
        logger.info(f"Template directory: {template_dir}")
    except ImportError:
        # If webwright is not installed, try to find the template in the current project structure
        template_dir = os.path.join(current_dir, 'webwright', 'templates', 'shell')
        logger.info(f"Template directory (fallback): {template_dir}")
    
    dockerfile_path = os.path.join(template_dir, 'Dockerfile')
    app_path = os.path.join(template_dir, 'app')
    requirements_path = os.path.join(template_dir, 'app', 'requirements.txt')
    
    # Check if necessary files exist
    if not all(os.path.exists(path) for path in [dockerfile_path, app_path, requirements_path]):
        return {
            "success": False,
            "message": f"Required files not found in {template_dir}"
        }
    
    try:
        if action == 'stop':
            stop_command = f"docker stop {container_name} && docker rm {container_name}"
            subprocess.run(stop_command, shell=True, check=True)
            logger.info(f"Container {container_name} stopped and removed successfully.")
            
            # Clean up the temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Temporary directory {temp_dir} cleaned up.")

            return {
                "success": True,
                "message": f"Container {container_name} stopped and removed successfully."
            }

        
        elif action == 'restart':
            stop_command = f"docker stop {container_name} && docker rm {container_name}"
            subprocess.run(stop_command, shell=True, check=True)
            logger.info(f"Container {container_name} stopped and removed successfully for restart.")
            action = 'start'  # Proceed to the start action after stopping
        
        if action == 'start' or action == 'recreate':
            # Clean up the temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Temporary directory {temp_dir} cleaned up.")

            # Create a temporary directory for our files
            os.makedirs(temp_dir, exist_ok=True)
            logger.info(f"Temporary directory created at: {temp_dir}")
            
            # Copy necessary files to temporary directory
            shutil.copy2(dockerfile_path, temp_dir)
            shutil.copytree(app_path, os.path.join(temp_dir, 'app'))
            shutil.copy2(requirements_path, temp_dir)
            logger.info(f"Copied necessary files to temporary directory.")
            
            # Change to the temporary directory
            os.chdir(temp_dir)
            logger.info(f"Changed to temporary directory: {temp_dir}")
            
            # Build Docker image
            build_command = f"docker build -t {image_name} ."
            subprocess.run(build_command, shell=True, check=True)
            logger.info(f"Docker image {image_name} built successfully.")
            
            # Start Docker container
            run_command = f"docker run -d --name {container_name} -p {port_mapping} {image_name}"
            subprocess.run(run_command, shell=True, check=True)
            logger.info(f"Container {container_name} started successfully. Access the app at http://localhost:7000")
            
            # Log the output
            log_command = f"docker logs -f {container_name}"
            with open(log_file, 'a') as log:
                subprocess.Popen(log_command, shell=True, stdout=log, stderr=log)
            
            return {
                "success": True,
                "message": f"Container {container_name} started successfully. Access the app at http://localhost:7000"
            }
        
        else:
            logger.error(f"Invalid action specified: {action}. Use 'start', 'stop', 'restart', or 'recreate'.")
            return {
                "success": False,
                "message": f"Invalid action specified: {action}. Use 'start', 'stop', 'restart', or 'recreate'."
            }
    
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred while running Docker commands: {str(e)}")
        return {
            "success": False,
            "message": f"An error occurred while running Docker commands: {str(e)}"
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return {
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }
    finally:
        # Change back to the original directory
        os.chdir(current_dir)
        logger.info(f"Changed back to the original directory: {current_dir}")
        
