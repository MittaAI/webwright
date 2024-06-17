# lib/functions/create_github_issue.py
import os
import subprocess
from github import Github
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger

logger = get_logger()

@function_info_decorator
def create_github_issue(issue_title: str, issue_body: str) -> dict:
    """
    Creates a new issue for the repository in the current directory.
    :param issue_title: The title of the issue.
    :type issue_title: str
    :param issue_body: The body content of the issue.
    :type issue_body: str
    :return: A dictionary containing the status of the operation and additional information.
    :rtype: dict
    """
    try:
        # Get the GitHub token from the environment variable
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            return {
                "success": False,
                "error": "GitHub token not found",
                "reason": "The 'GITHUB_TOKEN' environment variable is not set."
            }
        
        # Create a GitHub instance
        g = Github(github_token)
        
        # Get the repository name and organization/user from the remote URL
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode("utf-8").strip()
        repo_info = extract_repo_info(remote_url)
        
        if repo_info:
            org_name, repo_name = repo_info
            logger.info(f"Organization/User: {org_name}")
            logger.info(f"Repository: {repo_name}")
            
            # Get the repository
            repo = g.get_repo(f"{org_name}/{repo_name}")
            
            # Create a new issue
            issue = repo.create_issue(
                title=issue_title,
                body=issue_body
            )
            
            return {
                "success": True,
                "message": f"Issue '{issue_title}' created for repository '{org_name}/{repo_name}'",
                "issue_url": issue.html_url
            }
        else:
            return {
                "success": False,
                "error": "Failed to extract repository information",
                "reason": "Unable to determine the organization/user and repository name from the remote URL."
            }
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to create GitHub issue",
            "reason": str(e)
        }

def extract_repo_info(remote_url):
    print(remote_url)
    # Extract the organization/user and repository name from the remote URL
    
    if remote_url.startswith("https://github.com/"):
        org_repo = remote_url[len("https://github.com/"):]
    elif remote_url.startswith("git@github.com:"):
        org_repo = remote_url[len("git@github.com:"):]
    else:
        return None
    
    org_repo = org_repo.strip()
    if org_repo.endswith(".git"):
        org_repo = org_repo[:-4]
    
    print(org_repo)
    org_name, repo_name = org_repo.split("/")
    print(org_name, repo_name)
    return org_name, repo_name
