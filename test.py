import os
from git import Repo

# Automatically detect the current repository path
repo_path = os.getcwd()
commit_message = 'this is a commit'

# Initialize the repository
repo = Repo(repo_path)

# Check the repository's current status
if repo.is_dirty(untracked_files=True):
    # Add all changes to the staging area
    repo.git.add(A=True)

    # Commit the changes
    repo.index.commit(commit_message)

    # Push the changes to the remote repository
    origin = repo.remote(name='origin')
    origin.push()

    print("Changes have been committed and pushed to the remote repository.")
else:
    print("No changes to commit.")
