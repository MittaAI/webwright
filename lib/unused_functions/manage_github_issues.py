import os
from github import Github
from git import Repo  # Import from GitPython
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger
from lib.config import Config

logger = get_logger()

@function_info_decorator
def manage_github_issues(action: str, issue_number: int = None, issue_title: str = None, issue_body: str = None, comment_body: str = None, state: str = 'all') -> dict:
    """
    Allows the local Mitta agent to manage GitHub issues: lists issues, creates an issue, comments on an issue, and closes an issue.
    :param action: The action to perform: 'list', 'create', 'comment', or 'close'.
    :type action: str
    :param issue_number: The number of the issue to comment on or close (required for 'comment' and 'close' actions) (optional).
    :type issue_number: int
    :param issue_title: The title of the issue (required for 'create' action) (optional).
    :type issue_title: str
    :param issue_body: The body content of the issue (required for 'create' action) (optional).
    :type issue_body: str
    :param comment_body: The comment to add to an issue (required for 'comment' action) (optional).
    :type comment_body: str
    :param state: The state of the issues to list ('all', 'open', or 'closed'). Default is 'all' (optional).
    :type state: str
    :return: A dictionary containing the status of the operation and additional information.
    :rtype: dict
    """
    config = Config()

    try:
        # Assuming the get_github_token function has been defined and imported as described in the previous message.

        # Get the GitHub token
        token_info = config.get_github_token()
        github_token = token_info['token']
        if not github_token:
            return {
                "success": False,
                "error": "GitHub token not found",
                "reason": token_info['error'] or "Neither the 'GITHUB_TOKEN' environment variable nor the config provided a valid token."
            }

        # Create a GitHub instance
        g = Github(github_token)

        # Get the repository name and organization/user from the local Git configuration
        repo = Repo(".")
        remote_url = repo.remotes.origin.url
        repo_info = extract_repo_info(remote_url)

        if repo_info:
            org_name, repo_name = repo_info
            logger.info(f"Organization/User: {org_name}")
            logger.info(f"Repository: {repo_name}")

            # Get the repository
            repo = g.get_repo(f"{org_name}/{repo_name}")

            if action == 'list':
                # List issues in the repository based on the specified state
                issues = repo.get_issues(state=state)
                issues_list = [{"title": issue.title, "body": issue.body, "state": issue.state, "url": issue.html_url, "number": issue.number} for issue in issues]
                return {
                    "success": True,
                    "issues": issues_list,
                    "total_count": len(issues_list)
                }

            elif action == 'create':
                # Validate required fields for create action
                if not issue_title or not issue_body:
                    return {
                        "success": False,
                        "error": "Missing required fields",
                        "reason": "'issue_title' and 'issue_body' are required for creating an issue."
                    }

                # Create a new issue
                issue = repo.create_issue(
                    title=issue_title,
                    body=issue_body
                )
                return {
                    "success": True,
                    "message": f"Issue '{issue_title}' created for repository '{org_name}/{repo_name}'",
                    "issue_url": issue.html_url,
                    "issue_number": issue.number
                }

            elif action == 'comment':
                # Validate required fields for comment action
                if not issue_number or not comment_body:
                    return {
                        "success": False,
                        "error": "Missing required fields",
                        "reason": "'issue_number' and 'comment_body' are required for commenting on an issue."
                    }

                # Get the issue by number and add a comment
                issue = repo.get_issue(issue_number)
                issue.create_comment(body=comment_body)
                return {
                    "success": True,
                    "message": f"Comment added to issue '{issue.title}' (#{issue.number})",
                    "issue_url": issue.html_url,
                    "issue_number": issue.number
                }

            elif action == 'close':
                # Validate required field for close action
                if not issue_number:
                    return {
                        "success": False,
                        "error": "Missing required field",
                        "reason": "'issue_number' is required for closing an issue."
                    }

                # Get the issue by number and close it
                issue = repo.get_issue(issue_number)
                issue.edit(state="closed")
                return {
                    "success": True,
                    "message": f"Issue '{issue.title}' (#{issue.number}) closed",
                    "issue_url": issue.html_url,
                    "issue_number": issue.number
                }

            else:
                return {
                    "success": False,
                    "error": "Invalid action",
                    "reason": "The action must be 'list', 'create', 'comment', or 'close'."
                }
        else:
            return {
                "success": False,
                "error": "Failed to extract repository information",
                "reason": "Unable to determine the organization/user and repository name from the remote URL."
            }
    except Exception as e:
        error_message = f"Failed to manage GitHub issues: {str(e)}"
        logger.info(error_message, exc_info=True)

        return {
            "success": False,
            "error": "Failed to manage GitHub issues",
            "reason": str(e)
        }

def extract_repo_info(remote_url):
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

    parts = org_repo.split("/")
    if len(parts) != 2:
        return None

    org_name, repo_name = parts
    return org_name, repo_name