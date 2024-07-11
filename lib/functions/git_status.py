import os
from git import Repo
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def git_status(github_token: str = None) -> dict:
    """
    Retrieves the status of the current git repository and optionally the GitHub repository.

    :param github_token: The GitHub token to use for accessing the repository. Defaults to None.
    :type github_token: str
    :return: A dictionary containing the status of the git repository, repository name, and remote URL if applicable.
    :rtype: dict
    """
    try:
        # Automatically detect the current repository path
        repo_path = os.getcwd()

        # Initialize the repository
        repo = Repo(repo_path)

        # Get the git status
        git_status_output = repo.git.status()

        # Get the repository name
        repo_name = os.path.basename(repo_path)

        # Get the remote URL
        remote_url = repo.remotes.origin.url if repo.remotes else "No remote URL"

        # Prepare the response dictionary
        response = {
            "success": True,
            "git_status": git_status_output,
            "repository_name": repo_name,
            "remote_url": remote_url
        }

        # If a GitHub token is provided, get the repository URL
        if github_token:
            from github import Github

            g = Github(github_token)
            user = g.get_user()
            github_repo = user.get_repo(repo_name)

            response["github_repo_url"] = github_repo.html_url

        return response
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }