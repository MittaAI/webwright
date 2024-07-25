from git import Repo
from github import Github
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger
from lib.config import Config

logger = get_logger()

@function_info_decorator
def git_pull_request(pr_title: str, pr_body: str = None, branch_name: str = None) -> dict:
    """
    Creates a pull request on GitHub.
    
    :param pr_title: The title of the pull request.
    :type pr_title: str
    :param pr_body: The body content of the pull request. Defaults to None.
    :type pr_body: str
    :param branch_name: The name of the branch to create the pull request from. Defaults to the current branch.
    :type branch_name: str
    :return: A dictionary containing the status and any relevant details of the operation.
    :rtype: dict
    """

    config = Config()

    try:
        # Initialize the repository
        repo = Repo(".")
        
        # Get the current active branch
        current_branch = repo.active_branch
        
        # Use specified branch name or default to current branch
        branch_name = branch_name or current_branch.name
        
        # Get the GitHub token from environment or configuration
        token_info = config.get_github_token()
        github_token = token_info.get('token')
        
        if not github_token:
            return {"success": False, "error": "GitHub token not found or invalid. Pull request not created."}
        
        # Initialize GitHub API client
        g = Github(github_token)
        
        # Extract repository details from the remote URL
        remote_url = repo.remotes.origin.url
        org_name, repo_name = extract_repo_details(remote_url)
        
        if not org_name or not repo_name:
            return {"success": False, "error": "Failed to extract owner and repository name from remote URL."}
        
        # Get the GitHub repository and create the pull request
        github_repo = g.get_repo(f"{org_name}/{repo_name}")
        pr = github_repo.create_pull(title=pr_title, body=pr_body or '', head=branch_name, base='main')
        
        return {
            "success": True,
            "pull_request": {
                "url": pr.html_url,
                "number": pr.number,
                "state": pr.state
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to create pull request: {str(e)}", exc_info=True)
        return {"success": False, "error": "Failed to create pull request", "reason": str(e)}

def extract_repo_details(remote_url):
    # Extract the organization/user and repository name from the remote URL
    if remote_url.startswith("https://github.com/"):
        org_repo = remote_url[len("https://github.com/"):] 
    elif remote_url.startswith("git@github.com:"):
        org_repo = remote_url[len("git@github.com:"):] 
    else:
        return None, None

    org_repo = org_repo.strip()
    if org_repo.endswith(".git"):
        org_repo = org_repo[:-4]

    parts = org_repo.split("/")
    if len(parts) != 2:
        return None, None

    org_name, repo_name = parts
    return org_name, repo_name
