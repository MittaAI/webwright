import os
import subprocess
import shutil
import re
from lib.util import setup_logging, get_logger
from lib.function_wrapper import function_info_decorator

# Initialize logging
logger = setup_logging()

@function_info_decorator
def manage_app_container(action: str) -> dict:
    """
    Allows the local Mitta agent to manage a Docker container for an application, allowing the agent to start, stop, restart, and recreate container actions.

    Example: "start the app" would start the Docker container for the app if it wasn't running.

    :param action: The action to perform: 'start', 'stop', 'restart', or 'recreate'.
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    # Generate container name based on the current directory name
    current_dir = os.getcwd()
    project_name = os.path.basename(current_dir)
    container_name = f"{project_name.lower().replace(' ', '_')}_container"
    image_name = f"{project_name.lower().replace(' ', '_')}_image"
    
    # Paths
    log_directory = os.path.expanduser('~/.myapp/logs')
    log_file = os.path.join(log_directory, 'app.log')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    dockerfile_path = os.path.join(current_dir, 'Dockerfile')
    
    # Read Dockerfile and extract information
    if os.path.exists(dockerfile_path):
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Extract port from Dockerfile
        port_match = re.search(r'EXPOSE\s+(\d+)', dockerfile_content)
        if port_match:
            container_port = port_match.group(1)
            port_mapping = f"{container_port}:{container_port}"
        else:
            container_port = "5000"
            port_mapping = "5000:5000"  # Default if not found
        
        # Extract base image from Dockerfile (if specified)
        image_match = re.search(r'FROM\s+(.+)', dockerfile_content)
        if image_match:
            base_image = image_match.group(1)
            logger.info(f"Using base image: {base_image}")
    else:
        logger.error(f"Dockerfile not found at: {dockerfile_path}")
        return {
            "success": False,
            "message": f"Dockerfile not found at: {dockerfile_path}"
        }

    temp_dir = os.path.join(current_dir, 'app_temp')

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
            shutil.copytree(current_dir, temp_dir, dirs_exist_ok=True)
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
            logger.info(f"Container {container_name} started successfully. Access the app at http://localhost:{container_port}")
            
            # Log the output
            log_command = f"docker logs -f {container_name}"
            with open(log_file, 'a') as log:
                subprocess.Popen(log_command, shell=True, stdout=log, stderr=log)
            
            return {
                "success": True,
                "message": f"Container {container_name} started successfully. Access the app at http://localhost:{container_port}"
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