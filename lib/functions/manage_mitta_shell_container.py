from lib.function_wrapper import function_info_decorator
import subprocess
import os
import shutil
import random
import string
import pkg_resources

@function_info_decorator
def manage_mitta_shell_container(action: str) -> dict:
    """
    Allows the local Mitta agent to manages a Docker container for the Shell application and appliations the shell builds for the user, allowing start, stop, restart, and recreate actions.
    
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
    try:
        # Get the path to the installed templates directory
        template_dir = pkg_resources.resource_filename('webwright', 'templates/shell')
        print(template_dir)
    except ImportError:
        # If webwright is not installed, try to find the template in the current project structure
        template_dir = os.path.join(current_dir, 'webwright', 'templates', 'shell')
    
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
            return {
                "success": True,
                "message": f"Container {container_name} stopped and removed successfully."
            }
        
        elif action == 'restart':
            stop_command = f"docker stop {container_name} && docker rm {container_name}"
            subprocess.run(stop_command, shell=True, check=True)
            action = 'start'  # Proceed to the start action after stopping
        
        if action == 'start' or action == 'recreate':
            # Create a temporary directory for our files
            temp_dir = os.path.join(current_dir, 'mitta_shell_temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Copy necessary files to temporary directory
            shutil.copy2(dockerfile_path, temp_dir)
            shutil.copytree(app_path, os.path.join(temp_dir, 'app'))
            shutil.copy2(requirements_path, temp_dir)
            
            # Change to the temporary directory
            os.chdir(temp_dir)
            
            # Build Docker image
            build_command = f"docker build -t {image_name} ."
            subprocess.run(build_command, shell=True, check=True)
            
            # Start Docker container
            run_command = f"docker run -d --name {container_name} -p {port_mapping} {image_name}"
            subprocess.run(run_command, shell=True, check=True)
            
            return {
                "success": True,
                "message": f"Container {container_name} started successfully. Access the app at http://localhost:7000"
            }
        
        else:
            return {
                "success": False,
                "message": f"Invalid action specified: {action}. Use 'start', 'stop', 'restart', or 'recreate'."
            }
    
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "message": f"An error occurred while running Docker commands: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }
    finally:
        # Change back to the original directory
        os.chdir(current_dir)
        
        # Clean up the temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# The function is now defined but not automatically called
