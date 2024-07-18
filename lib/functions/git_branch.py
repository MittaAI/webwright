from git import Repo, GitCommandError
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger

logger = get_logger()

@function_info_decorator
def git_branch(action: str, branch_name: str = None, new_branch_name: str = None) -> dict:
    """
    Manages git branch operations: create, list, checkout, and delete.
    
    :param action: The action to perform: 'create', 'list', 'checkout', or 'delete'.
    :type action: str
    :param branch_name: The name of the branch (used in 'checkout', 'delete').
    :type branch_name: str
    :param new_branch_name: The name of the new branch to create (used in 'create').
    :type new_branch_name: str
    :return: A dictionary containing the status of the operation and any relevant messages.
    :rtype: dict
    """
    try:
        repo = Repo(".")
        
        if action == 'create':
            if not new_branch_name:
                return {"success": False, "error": "New branch name is required"}
            repo.git.branch(new_branch_name)
            return {"success": True, "message": f"Branch '{new_branch_name}' created"}
        elif action == 'list':
            branches = [head.name for head in repo.heads]
            return {"success": True, "branches": branches}
        elif action == 'checkout':
            if not branch_name:
                return {"success": False, "error": "Branch name is required"}
            repo.git.checkout(branch_name)
            return {"success": True, "message": f"Checked out to branch '{branch_name}'"}
        elif action == 'delete':
            if not branch_name:
                return {"success": False, "error": "Branch name is required"}
            repo.git.branch('-d', branch_name)
            return {"success": True, "message": f"Branch '{branch_name}' deleted"}
        else:
            return {"success": False, "error": "Invalid action"}
    except GitCommandError as e:
        logger.error(f"Git command failed: {str(e)}", exc_info=True)
        return {"success": False, "error": "Git command failed", "reason": str(e)}
    except Exception as e:
        logger.error(f"An unexpected error occurred during git branch operation: {str(e)}", exc_info=True)
        return {"success": False, "error": "An unexpected error occurred", "reason": str(e)}
