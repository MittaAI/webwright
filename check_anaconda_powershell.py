import os

# Function to check if 'conda init powershell' is needed
 def check_conda_powershell():
    conda_init_done = os.popen('conda info').read()
    if 'active environment' not in conda_init_done.lower():
        print("It appears that 'conda init powershell' is needed. Please run the following command from the condabin directory:")
        print("./conda init powershell")
    else:
        print("Conda initialization for PowerShell is already set up.")

if __name__ == '__main__':
    check_conda_powershell()
