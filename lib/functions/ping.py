import subprocess
import platform
from lib.function_wrapper import function_info_decorator

def get_ping_command(host: str, count: int = 4) -> list:
    """
    Returns the appropriate ping command based on the operating system.
    """
    if platform.system().lower() == "windows":
        return ["ping", "-n", str(count), host]
    else:  # Unix-based systems (Linux, macOS)
        return ["ping", "-c", str(count), host]

@function_info_decorator
def ping(host: str = "google.com", count: int = 4) -> dict:
    """
    Pings a specified host (default is google.com) and returns the result.
    
    This function uses the system's ping command to check the connectivity and 
    response time of a specified host. It works on Windows, macOS, and Linux.
    
    :param host: The hostname or IP address to ping (default is "google.com")
    :type host: str
    :param count: The number of ping requests to send (default is 4)
    :type count: int
    :return: A dictionary containing the success status, ping results, and any relevant messages.
    :rtype: dict
    """
    ping_command = get_ping_command(host, count)
    
    try:
        # Run the ping command and capture the output
        result = subprocess.run(ping_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse the output to extract relevant information
            lines = result.stdout.split('\n')
            summary = next((line for line in reversed(lines) if line.strip()), '')
            
            return {
                "success": True,
                "message": f"Successfully pinged {host}",
                "output": result.stdout,
                "summary": summary
            }
        else:
            return {
                "success": False,
                "message": f"Failed to ping {host}",
                "output": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": f"Ping to {host} timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred while trying to ping {host}: {str(e)}"
        }