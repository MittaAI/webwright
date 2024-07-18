from git import Repo
from github import Github
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger, get_github_token

logger = get_logger()

@function_info_decorator
def git_commit_and_push(commit_message: str, branch_name: str = None, pr_title: str = None, pr_body: str = None) -> dict:
    """
    Automatically stages all changes, commits them with the provided message,
    pushes the changes to the remote repository, and optionally creates a pull request.

    This function adds all current changes to the staging area, commits them with the provided message from git_staus and git_diff.

    :param commit_message: The commit message to use for the commit. (built from summary of changes from git_diff).
    :type commit_message: str
    :param branch_name: The branch name to create and push to. If None, uses the current branch.
    :type branch_name: str
    :param pr_title: The title of the pull request. If None, no PR is created.
    :type pr_title: str
    :param pr_body: The body of the pull request. Defaults to None.
    :type pr_body: str
    :return: A dictionary containing the status of the commit, push, and pull request operation.
    :rtype: dict
    """
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

            response = {
                "success": True,
                "message": f"Changes have been committed and pushed to the remote branch '{branch_name}'."
            }

            # Get the GitHub token from environment or configuration
            token_info = get_github_token()
            github_token = token_info.get('token')

            # Create a pull request if a GitHub token is provided and pr_title is set
            if github_token and pr_title:
                g = Github(github_token)
                remote_url = repo.remotes.origin.url
                org_name, repo_name = extract_repo_details(remote_url)
                if org_name and repo_name:
                    github_repo = g.get_repo(f"{org_name}/{repo_name}")
                    pr = github_repo.create_pull(title=pr_title, body=pr_body or '', head=branch_name, base='main')
                    response['pull_request'] = {
                        'url': pr.html_url,
                        'number': pr.number,
                        'state': pr.state
                    }
                else:
                    logger.error("Failed to extract owner and repository name from remote URL.")
            elif pr_title:
                logger.warning("GitHub token not found or invalid. Pull request not created.")

            return response
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