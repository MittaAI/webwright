# lib/functions/git_commit_and_push.py
import os
from git import Repo
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def git_commit_and_push(commit_message: str = "Automated commit") -> dict:
    """
    Automatically stages all changes, commits them with the provided message, and pushes the changes to the remote repository.

    :param commit_message: The commit message to use for the commit. Defaults to "Automated commit".
    :type commit_message: str
    :return: A dictionary containing the status of the commit and push operation.
    :rtype: dict
    """
    try:
        # Automatically detect the current repository path
        repo_path = os.getcwd()

        # Initialize the repository
        repo = Repo(repo_path)

        # Check the repository's current status
        if repo.is_dirty(untracked_files=True):
            # Add all changes to the staging area
            repo.git.add(A=True)

            # Commit the changes
            repo.index.commit(commit_message)

            # Push the changes to the remote repository
            origin = repo.remote(name='origin')
            origin.push()

            return {
                "success": True,
                "message": "Changes have been committed and pushed to the remote repository."
            }
        else:
            return {
                "success": True,
                "message": "No changes to commit."
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
