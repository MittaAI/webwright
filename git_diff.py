import subprocess


def git_diff():
    """
    Performs a git diff for the current repository.

    This function uses the subprocess module to execute the 'git diff' command
    and capture its output. If the command executes successfully, the function
    returns the diff output as a string. If an error occurs during the execution
    of the command, the function returns an error message along with the exception
    details.

    Returns:
        str: The git diff output if the command executes successfully, or an error
             message if an exception occurs.

    Raises:
        subprocess.CalledProcessError: If the 'git diff' command fails to execute.
    """
    try:
        result = subprocess.run(['git', 'diff', '--cached'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_message = f"Error executing git diff: {e}"
        return error_message


if __name__ == "__main__":
    diff_output = git_diff()
    print(diff_output)
