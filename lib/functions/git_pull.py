from git import Repo
from git.exc import GitCommandError
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger

logger = get_logger()

@function_info_decorator
def git_pull(branch_name: str = None, remote_name: str = 'origin') -> dict:
    """
    Performs a git pull operation to fetch and merge changes from the remote repository for the current branch.
    If a branch name is specified, it ensures that's the current branch before pulling.

    :param branch_name: The name of the branch to pull. If None, pulls the current branch. Defaults to None.
    :type branch_name: str
    :param remote_name: The name of the remote to pull from. Defaults to 'origin'.
    :type remote_name: str
    :return: A dictionary containing the status of the pull operation and any relevant messages.
    :rtype: dict
    """
    try:
        # Initialize the repository
        repo = Repo(".")

        # Get the current active branch
        current_branch = repo.active_branch

        # Check if the specified branch matches the current branch
        if branch_name and branch_name != current_branch.name:
            return {
                "success": False,
                "error": f"Specified branch '{branch_name}' is not the current branch. Current branch is '{current_branch.name}'.",
                "current_branch": current_branch.name
            }

        # Use the current branch name if none was specified
        branch_name = branch_name or current_branch.name

        # Get the remote
        remote = repo.remote(name=remote_name)

        # Perform the pull operation
        pull_info = remote.pull(branch_name)

        # Check the result of the pull operation
        if pull_info:
            fetch_info = pull_info[0]
            if fetch_info.note == "up to date":
                message = f"Branch '{branch_name}' is already up to date."
            elif fetch_info.note == "fast forward":
                message = f"Successfully pulled changes into '{branch_name}'. Fast-forward."
            elif fetch_info.note == "merged":
                message = f"Successfully pulled and merged changes into '{branch_name}'."
            else:
                message = f"Pull operation completed, but status is unclear. Please check the repository."
            
            return {
                "success": True,
                "message": message,
                "current_branch": branch_name
            }
        else:
            return {
                "success": False,
                "error": "Pull operation failed with no error message.",
                "current_branch": branch_name
            }

    except GitCommandError as e:
        logger.error(f"Git pull command failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Git pull command failed",
            "reason": str(e),
            "current_branch": repo.active_branch.name
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred during git pull: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred during git pull",
            "reason": str(e),
            "current_branch": repo.active_branch.name
        }
