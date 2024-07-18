import os

def check_github_token():
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return 'GitHub token is set.'
    else:
        return 'GitHub token is NOT set.'

if __name__ == '__main__':
    print(check_github_token())