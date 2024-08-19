from git import Repo
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger
from lib.config import Config

logger = get_logger()

@function_info_decorator
def git_commit_and_push(commit_message: str, branch_name: str = None) -> dict:
    """
    Automatically stages all changes, commits them with the provided message,
    and pushes the changes to the remote repository.

    This function adds all current changes to the staging area, commits them with the provided message from git_staus and git_diff.

    :param commit_message: The commit message to use for the commit. (built from summary of changes from git_diff).
    :type commit_message: str
    :param branch_name: The branch name to create and push to. If None, uses the current branch.
    :type branch_name: str
    :return: A dictionary containing the status of the commit and push operation.
    :rtype: dict
    """

    config = Config()

    try:
        # Initialize the repository
        repo = Repo(".")

        # Get the current active branch
        current_branch = repo.active_branch

        # Create and checkout the branch if specified
        if branch_name:
            if branch_name in repo.heads:
                branch = repo.heads[branch_name]
            else:
                # Create a new branch from the current branch
                branch = current_branch.checkout(b=branch_name)

            # Ensure we're on the desired branch
            if repo.active_branch != branch:
                branch.checkout()
        else:
            branch_name = current_branch.name

        # Check the repository's current status
        if repo.is_dirty(untracked_files=True):
            # Add all changes to the staging area
            repo.git.add(A=True)

            # Commit the changes
            repo.index.commit(commit_message)

            # Push the changes to the remote repository
            origin = repo.remote(name='origin')
            origin.push(refspec=f'{branch_name}:{branch_name}')

            return {
                "success": True,
                "message": f"Changes have been committed and pushed to the remote branch '{branch_name}'."
            }
        else:
            return {
                "success": False,
                "message": "There are no changes to commit."
            }
    except Exception as e:
        logger.error(f"Failed to commit and push changes: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to commit and push changes",
            "reason": str(e)
        }
