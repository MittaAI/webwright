import subprocess


def git_commit_and_push(commit_message: str = "Automated commit") -> dict:
    """
    Automatically stages all changes, commits them with the provided message, generates a changelog,
    saves it in the changelog directory with a timestamp filename, and pushes the changes to the remote repository.
    NOTE: The LLM should use the git_diff function first to get a good commit message.

    :param commit_message: The commit message to use for the commit. Defaults to "Automated commit".
    :type commit_message: str
    :return: A dictionary containing the success status and any output or errors encountered.
    :rtype: dict
    """
    try:
        # Stage all changes
        subprocess.run(['git', 'add', '.'], check=True)

        # Commit the changes with the provided message
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push the changes to the remote repository
        subprocess.run(['git', 'push'], check=True)

        return {"success": True, "message": "Changes committed and pushed successfully."}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": str(e)}
