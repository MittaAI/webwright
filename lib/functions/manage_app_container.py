import os
import subprocess
import re
from lib.util import setup_logging, get_logger
from lib.function_wrapper import function_info_decorator

# Initialize logging
logger = setup_logging()

@function_info_decorator
def manage_app_container(action: str, app_path: str, port: int) -> dict:
    """
    Allows the local Mitta agent to manage a Docker container for an application, allowing the agent to start, stop, restart, and recreate container actions.

    Example: "start the app" would start the Docker container for the app if it wasn't running.

    :param action: The action to perform: 'start', 'stop', 'restart', or 'recreate'.
    :param app_path: The path to the application directory.
    :param port: The port number on which the application should run.
    :return: A dictionary containing the success status and any relevant messages.
    :rtype: dict
    """
    original_dir = os.getcwd()

    try:
        # Change to the application directory
        os.chdir(app_path)
        logger.info(f"Changed to application directory: {app_path}")

        # Generate container name based on the application directory name
        project_name = os.path.basename(app_path)
        container_name = f"{project_name.lower().replace(' ', '_')}_container"
        image_name = f"{project_name.lower().replace(' ', '_')}_image"

        # Set up logging
        log_directory = os.path.expanduser(f'~/.webwright/apps/{project_name}')
        log_file = os.path.join(log_directory, f'{project_name}.log')
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        # Ensure Dockerfile exists in the current directory
        if not os.path.exists('Dockerfile'):
            logger.error("Dockerfile not found in the current directory")
            return {
                "success": False,
                "message": "Dockerfile not found in the current directory"
            }
        

        # Output the port information before executing any commands
        port = None
        with open('Dockerfile', 'r') as dockerfile:
            for line in dockerfile:
                match = re.search(r"EXPOSE (\d+)", line)
                if match:
                    port = match.group(1)
                    break
        if not port:
            logger.error("Port not found in the Dockerfile.")
            return {
                "success": False,
                "message": "Port not found in the Dockerfile."
            }
        logger.info(f"Detected port: {port}")

        if action == 'stop':
            stop_command = f"docker stop {container_name} && docker rm {container_name}"
            subprocess.run(stop_command, shell=True, check=True)
            logger.info(f"Container {container_name} stopped and removed successfully.")

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
            # Build Docker image
            build_command = f"docker build -t {image_name} ."
            subprocess.run(build_command, shell=True, check=True)
            logger.info(f"Docker image {image_name} built successfully.")
            
            # Start Docker container
            port_mapping = f"{port}:{port}"
            run_command = f"docker run -d --name {container_name} -p {port_mapping} {image_name}"
            subprocess.run(run_command, shell=True, check=True)
            
            logger.info(f"Container {container_name} started successfully. Access the app at http://localhost:{port}")
            
            # Log the output
            log_command = f"docker logs -f {container_name}"
            with open(log_file, 'a') as log:
                subprocess.Popen(log_command, shell=True, stdout=log, stderr=log)
            
            return {
                "success": True,
                "message": f"Container {container_name} started successfully. Access the app at http://localhost:{port}"
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
        os.chdir(original_dir)
        logger.info(f"Changed back to the original directory: {original_dir}")
