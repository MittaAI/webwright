import os
from typing import List, Dict

def fetch_command_details(command: str) -> Dict[str, str]:
    # This function now reads the content of the JS file to extract details
    file_path = os.path.join('templates', 'commands', f"{command}.js")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            # Here you could parse the content to extract more details
            # For now, we'll just use the first line as the "line" detail
            first_line = content.split('\n')[0] if content else "No description available"
        return {
            "name": command,
            "command": f"!{command}",
            "line": first_line.strip('// ')  # Assuming comments start with //
        }
    return {
        "name": command,
        "command": f"!{command}",
        "line": f"No details available for {command}"
    }

def build_command_list() -> List[Dict[str, str]]:
    command_dicts = []
    commands_dir = os.path.join('templates', 'commands')
    
    if os.path.exists(commands_dir):
        for file in sorted(os.scandir(commands_dir), key=lambda e: e.name):
            if file.name.endswith('.js'):
                command_name = file.name[:-3]  # Remove .js extension
                command_details = fetch_command_details(command_name)
                command_dicts.append(command_details)
    else:
        print(f"Warning: Directory {commands_dir} does not exist.")
    
    return command_dicts