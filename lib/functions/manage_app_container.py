import os
import subprocess
import re
import shutil
import random
from lib.util import setup_main_logging, get_logger
from lib.function_wrapper import function_info_decorator

# Initialize logging
logger = setup_main_logging()

# Find Docker and Docker Compose executables
DOCKER_PATH = shutil.which("docker")
DOCKER_COMPOSE_PATH = shutil.which("docker-compose")

@function_info_decorator
def manage_app_container(action: str, app_path: str, port: int = None) -> dict:
    """
    Manages Docker container actions: start, stop, restart, and recreate.
    Prioritizes using Docker Compose if a docker-compose.yml file is present.
    Assigns a random port between 8100 and 8200 if not provided when using Dockerfile.

    :param action: The action to perform: 'start', 'stop', 'restart', or 'recreate'.
    :param app_path: The path to the application directory.
    :param port: The port number on which the application should run (optional, used only for Dockerfile).
    :return: A dictionary containing the success status and any relevant messages.
    """
    original_dir = os.getcwd()
    docker_compose_file = os.path.join(app_path, 'docker-compose.yml')

    if not DOCKER_PATH:
        return {"success": False, "message": "Docker executable not found. Please ensure Docker is installed and in your PATH."}

    try:
        os.chdir(app_path)
        logger.info(f"Changed to application directory: {app_path}")

        if os.path.exists(docker_compose_file):
            return _handle_docker_compose(action)
        else:
            if port is None:
                port = random.randint(8100, 8200)
                logger.info(f"Assigned random port: {port}")
            return _handle_docker(action, app_path, port)

    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred while running Docker commands: {str(e)}")
        return {"success": False, "message": f"An error occurred while running Docker commands: {str(e)}"}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return {"success": False, "message": f"An unexpected error occurred: {str(e)}"}
    finally:
        os.chdir(original_dir)
        logger.info(f"Changed back to the original directory: {original_dir}")

def _handle_docker_compose(action: str) -> dict:
    if not DOCKER_COMPOSE_PATH:
        return {"success": False, "message": "Docker Compose executable not found. Please ensure Docker Compose is installed and in your PATH."}

    try:
        if action in ['stop', 'restart']:
            subprocess.run([DOCKER_COMPOSE_PATH, "down"], check=True)
            logger.info("Docker Compose services stopped successfully.")
            if action == 'stop':
                return {"success": True, "message": "Docker Compose services stopped successfully."}

        if action in ['start', 'recreate', 'restart']:
            subprocess.run([DOCKER_COMPOSE_PATH, "up", "--build", "-d"], check=True)
            logger.info("Docker Compose services started successfully.")
            return {"success": True, "message": "Docker Compose services started successfully."}

    except subprocess.CalledProcessError as e:
        logger.error(f"Docker Compose command failed: {e}")
        return {"success": False, "message": f"Docker Compose command failed: {e}"}

def _handle_docker(action: str, app_path: str, port: int) -> dict:
    project_name = os.path.basename(os.path.abspath(app_path))
    container_name = f"{project_name.lower().replace(' ', '_')}_container"
    image_name = f"{project_name.lower().replace(' ', '_')}_image"

    if not os.path.exists('Dockerfile'):
        return {"success": False, "message": "Dockerfile not found in the current directory"}

    dockerfile_port = _get_port_from_dockerfile()
    if not dockerfile_port:
        return {"success": False, "message": "Port not found in the Dockerfile."}

    try:
        if action in ['stop', 'restart']:
            subprocess.run([DOCKER_PATH, "stop", container_name], check=True)
            subprocess.run([DOCKER_PATH, "rm", container_name], check=True)
            logger.info(f"Container {container_name} stopped and removed successfully.")
            if action == 'stop':
                return {"success": True, "message": f"Container {container_name} stopped and removed successfully."}

        if action in ['start', 'recreate', 'restart']:
            subprocess.run([DOCKER_PATH, "build", "-t", image_name, "."], check=True)
            logger.info(f"Docker image {image_name} built successfully.")

            subprocess.run([
                DOCKER_PATH, "run", "-d", "--name", container_name,
                "-p", f"{port}:{dockerfile_port}",
                image_name
            ], check=True)

            logger.info(f"Container {container_name} started successfully. Access the app at http://localhost:{port}")
            return {
                "success": True,
                "message": f"Container {container_name} started successfully. Access the app at http://localhost:{port}"
            }

    except subprocess.CalledProcessError as e:
        logger.error(f"Docker command failed: {e}")
        return {"success": False, "message": f"Docker command failed: {e}"}

def _get_port_from_dockerfile() -> str:
    with open('Dockerfile', 'r') as dockerfile:
        for line in dockerfile:
            match = re.search(r"EXPOSE (\d+)", line)
            if match:
                return match.group(1)
    return None