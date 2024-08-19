import os
from git import Repo
from github import Github
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger
from lib.config import Config

logger = get_logger()

@function_info_decorator
def git_status() -> dict:
    """
    Retrieves the status of the current git repository and optionally the GitHub repository.
    Uses the GitHub token from environment or configuration to access GitHub repository details if available.
    
    :return: A dictionary containing the status of the git repository, repository name, and remote URL if applicable.
    :rtype: dict
    """

    config = Config()

    try:
        # Automatically detect the current repository path
        repo = Repo(".")
        git_status_output = repo.git.status()
        remote_url = repo.remotes.origin.url if repo.remotes else "No remote URL"
        org_name, repo_name = extract_repo_details(remote_url)
        
        response = {
            "success": True,
            "git_status": git_status_output,
            "repository_name": repo_name,
            "remote_url": remote_url
        }

        # Get the GitHub token from environment or configuration
        token_info = config.get_github_token()
        github_token = token_info.get('token')

        if github_token:
            g = Github(github_token)
            if org_name and repo_name:
                github_repo = g.get_repo(f"{org_name}/{repo_name}")
                response['github_repo_url'] = github_repo.html_url
            else:
                logger.error("Failed to extract owner and repository name from remote URL.")
        else:
            logger.error("GitHub token not found or invalid: " + token_info.get('error', 'No error message provided'))

        return response
    except Exception as e:
        logger.error("Failed to retrieve git status: " + str(e), exc_info=True)
        return {
            "success": False,
            "error": "Failed to retrieve git status",
            "reason": str(e)
        }


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
