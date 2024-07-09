import subprocess

def git_commit_and_push(commit_message: str = 'Automated commit') -> dict:
    try:
        # Stage all changes
        subprocess.run(['git', 'add', '--all'], check=True)

        # Commit changes
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push changes to the remote repository
        subprocess.run(['git', 'push'], check=True)

        return {'success': True, 'message': 'Changes committed and pushed successfully.'}
    except subprocess.CalledProcessError as e:
        return {'success': False, 'error': str(e)}

# Usage
if __name__ == "__main__":
    import sys
    commit_msg = 'Automated commit' if len(sys.argv) < 2 else sys.argv[1]
    result = git_commit_and_push(commit_msg)
    if result['success']:
        print(result['message'])
    else:
        print(f"Error: {result['error']}")