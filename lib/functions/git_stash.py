from git import Repo
from git.exc import GitCommandError
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger

logger = get_logger()

@function_info_decorator
def git_stash() -> dict:
    """
    Performs a git stash operation to stash the current changes in the repository.

    :return: A dictionary containing the status of the stash operation and any relevant messages.
    :rtype: dict
    """
    try:
        # Initialize the repository
        repo = Repo(".")

        # Perform the stash operation
        stash_result = repo.git.stash('save')

        if "No local changes" in stash_result:
            message = "No local changes to stash."
        else:
            message = "Changes have been stashed successfully."

        return {
            "success": True,
            "message": message
        }

    except GitCommandError as e:
        logger.error(f"Git stash command failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Git stash command failed",
            "reason": str(e)
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred during git stash: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred during git stash",
            "reason": str(e)
        }
