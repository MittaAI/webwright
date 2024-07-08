import os
from git import Repo
from datetime import datetime
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def git_commit_and_push(commit_message: str = "Automated commit") -> dict:
    """
    Automatically stages all changes, commits them with the provided message, generates a changelog,
    saves it in the changelog directory with a timestamp filename, and pushes the changes to the remote repository.

    :param commit_message: The commit message to use for the commit. Defaults to "Automated commit".
    :type commit_message: str
    :return: A dictionary containing the status of the commit and push operation.
    :rtype: dict
    """
    try:
        # Automatically detect the current repository path
        repo_path = os.getcwd()

        # Initialize the repository
        repo = Repo(repo_path)

        # Get the current date and time for the log filename
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M")
        changelog_filename = f"changelog_{timestamp}.txt"
        changelog_dir = os.path.join(repo_path, 'changelog')
        changelog_path = os.path.join(changelog_dir, changelog_filename)

        # Ensure the changelog directory exists
        os.makedirs(changelog_dir, exist_ok=True)

        # Get the git diff output
        diff_output = repo.git.diff('HEAD')

        # Write the changelog if there are changes
        if diff_output:
            with open(changelog_path, 'w') as changelog_file:
                changelog_file.write("# Changelog\n\n")
                changelog_file.write(f"## {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
                changelog_file.write("### Changes\n")
                changelog_file.write(diff_output)

        # Check the repository's current status
        if repo.is_dirty(untracked_files=True):
            # Add all changes to the staging area
            repo.git.add(A=True)

            # Commit the changes
            repo.index.commit(commit_message)

            # Push the changes to the remote repository
            origin = repo.remote(name='origin')
            origin.push()

            return {
                "success": True,
                "message": "Changes have been committed and pushed to the remote repository."
            }
        else:
            return {
                "success": True,
                "message": "No changes to commit."
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
