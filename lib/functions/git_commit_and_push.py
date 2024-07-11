import os
from datetime import datetime
from git import Repo
from github import Github  # Using PyGitHub for PR creation
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def git_commit_and_push(commit_message: str = "Automated commit", branch_name: str = None, github_token: str = None, pr_title: str = None, pr_body: str = None) -> dict:
    """
    Automatically stages all changes, commits them with the provided message, generates a changelog,
    saves it in the changelog directory with a timestamp filename, pushes the changes to the remote repository,
    and optionally creates a pull request if a GitHub token is provided.

    :param commit_message: The commit message to use for the commit. Defaults to "Automated commit".
    :type commit_message: str
    :param branch_name: The branch name to create and push to. Defaults to None.
    :type branch_name: str
    :param github_token: The GitHub token to use for creating pull requests. Defaults to None.
    :type github_token: str
    :param pr_title: The title of the pull request. Defaults to None.
    :type pr_title: str
    :param pr_body: The body of the pull request. Defaults to None.
    :type pr_body: str
    :return: A dictionary containing the status of the commit, push, and pull request operation.
    :rtype: dict
    """
    try:
        # Automatically detect the current repository path
        repo_path = os.getcwd()

        # Initialize the repository
        repo = Repo(repo_path)

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

        # Get the current date and time for the log filename
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M")
        changelog_filename = f"changelog_{timestamp}.txt"
        changelog_dir = os.path.join(repo_path, 'changelog')
        changelog_path = os.path.join(changelog_dir, changelog_filename)

        # Ensure the changelog directory exists
        os.makedirs(changelog_dir, exist_ok=True)

        # Write the commit message to the changelog
        with open(changelog_path, 'w') as changelog_file:
            changelog_file.write("# Changelog\n\n")
            changelog_file.write(f"## {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            changelog_file.write("### Changes\n")
            changelog_file.write(commit_message)

        # Note: To get the actual diff, run git_diff.py separately

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

            # Create a pull request if a GitHub token is provided
            if github_token and pr_title:
                g = Github(github_token)
                user = g.get_user()
                repo = user.get_repo(os.path.basename(repo_path))
                pr = repo.create_pull(title=pr_title, body=pr_body or '', head=branch_name, base='main')
                response['pull_request'] = {
                    'url': pr.html_url,
                    'number': pr.number,
                    'state': pr.state
                }

            return response
        else:
            return {
                "success": False,
                "message": "There are no changes to commit."
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }