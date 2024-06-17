import subprocess

def run_git_diff():
    try:
        # Run the 'git diff' command and capture the output
        output = subprocess.check_output(['git', 'diff'], stderr=subprocess.STDOUT, universal_newlines=True)
        
        # Print the output
        print("Git Diff Output:")
        print(output)
    except subprocess.CalledProcessError as e:
        print("Error executing 'git diff':")
        print(e.output)

# Run the 'git diff' command
run_git_diff()