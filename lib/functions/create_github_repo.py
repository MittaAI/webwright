import os
from github import Github
from lib.function_wrapper import function_info_decorator
from lib.config import Config

@function_info_decorator
def create_github_repo(repo_name: str, description: str, readme_content: str, license: str = "bsd-3-clause") -> dict:
    """
    Creates a new repository on GitHub and checks it out to a local directory.

    :param repo_name: The name of the repository to be created.
    :type repo_name: str
    :param description: The description of the repository.
    :type description: str
    :param readme_content: The content of the README file.
    :type readme_content: str
    :param license: The license to be used for the repository. Defaults to "bsd-3-clause".
    :type license: str
    :return: A dictionary containing the status of the operation and additional information.
    :rtype: dict
    """
    try:
        config = Config()
        # Get the GitHub token from the environment variable
        github_token = config.get_github_token()
        if not github_token:
            return {
                "success": False,
                "error": "GitHub token not found",
                "reason": "The 'GITHUB_TOKEN' environment variable is not set."
            }

        # Create a GitHub instance
        g = Github(github_token.get('token'))

        # Get the authenticated user
        user = g.get_user()

        # Create a new repository
        repo = user.create_repo(repo_name, description=description, license_template=license)

        # Create a local directory with the repository name
        local_repo_path = os.path.join(os.getcwd(), repo_name)
        os.makedirs(local_repo_path, exist_ok=True)

        # Clone the repository to the local directory
        repo.clone_url = repo.clone_url.replace("https://", f"https://{github_token}@")
        repo_clone = Repo.clone_from(repo.clone_url, local_repo_path)

        # Create a README file
        readme_file_path = os.path.join(local_repo_path, "README.md")
        with open(readme_file_path, "w") as readme_file:
            readme_file.write(readme_content)

        # Commit and push the changes
        repo_clone.index.add(["README.md"])
        repo_clone.index.commit("Initial commit")
        origin = repo_clone.remote("origin")
        origin.push()

        return {
            "success": True,
            "message": f"Repository '{repo_name}' created and checked out to '{local_repo_path}'",
            "repo_url": repo.html_url
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to create GitHub repository",
            "reason": str(e)
        }
