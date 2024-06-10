param(
    [string]$pythonVersion = "3.8",
    [string]$requirementsFile = "requirements.txt"
)

# Get the name of the root directory (checked out project path name)
$projectPath = Get-Location
$envName = Split-Path -Leaf $projectPath

# Function to check if a conda environment exists
function Test-CondaEnvExists {
    param(
        [string]$envName
    )
    $envs = conda env list | Select-String -Pattern $envName
    return $envs -ne $null
}

# Function to create a new conda environment
function New-CondaEnv {
    param(
        [string]$envName,
        [string]$pythonVersion
    )
    Write-Output "Creating new conda environment: $envName"
    conda create -y --name $envName python=$pythonVersion
}

# Function to install requirements
function Install-Requirements {
    param(
        [string]$envName,
        [string]$requirementsFile
    )
    Write-Output "Installing packages from $requirementsFile"
    conda run -n $envName pip install -r $requirementsFile
}

# Function to install Git using Conda
function Install-Git {
    param(
        [string]$envName
    )
    Write-Output "Git is not installed. Installing Git..."
    conda install -y -n $envName -c anaconda git
}

# Function to list SSH keys
function List-SSHKeys {
    $sshDirectory = "$HOME\.ssh"
    if (-not (Test-Path -Path $sshDirectory)) {
        Write-Error "No .ssh directory found in $HOME"
        exit 1
    }
    $keys = Get-ChildItem -Path $sshDirectory -File | Where-Object { $_.Extension -eq '' }
    if ($keys.Count -eq 0) {
        Write-Error "No SSH keys found in $sshDirectory"
        exit 1
    }
    Write-Output "Available SSH keys:"
    $i = 0
    foreach ($key in $keys) {
        Write-Output "$($i): $($key.Name)"
        $i++
    }
}

# Function to prompt user to select an SSH key
function Select-SSHKey {
    $sshDirectory = "$HOME\.ssh"
    $keys = Get-ChildItem -Path $sshDirectory -File | Where-Object { $_.Extension -eq '' }
    $selection = Read-Host "Enter the number of the SSH key to use"
    if ($selection -notmatch '^\d+$' -or [int]$selection -ge $keys.Count) {
        Write-Error "Invalid selection"
        exit 1
    }
    return $keys[$selection].FullName
}

# Function to configure SSH for the selected key
function Configure-SSH {
    param(
        [string]$selectedKey
    )
    $sshConfigFile = "$HOME\.ssh\config"
    if (-not (Test-Path -Path $sshConfigFile)) {
        New-Item -Path $sshConfigFile -ItemType File -Force
    }
    $sshConfigContent = @"
Host github.com
  HostName github.com
  User git
  IdentityFile $selectedKey
  IdentitiesOnly yes
"@
    Set-Content -Path $sshConfigFile -Value $sshConfigContent
    Write-Output "SSH configuration updated."

    # Set the global core.sshCommand to use the selected key
    git config --global core.sshCommand "ssh -i $selectedKey"
    Write-Output "Global SSH command configuration updated."
}

# Main script
if (-not (Test-Path -Path "$env:CONDA_EXE")) {
    Write-Error "Conda is not installed or not found in the system PATH."
    exit 1
}

if (Test-CondaEnvExists -envName $envName) {
    Write-Output "Conda environment '$envName' already exists."
} else {
    New-CondaEnv -envName $envName -pythonVersion $pythonVersion
}

Write-Output "Activating conda environment: $envName"
conda activate $envName

# Check if Git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Install-Git -envName $envName
} else {
    Write-Output "Git is already installed."
}

if (Test-Path -Path $requirementsFile) {
    Install-Requirements -envName $envName -requirementsFile $requirementsFile
} else {
    Write-Warning "Requirements file '$requirementsFile' not found. Skipping package installation."
}

# Function to update the .webwright_config file with the SSH key
function Update-WebrightConfigSSHKey {
    param(
        [string]$configFile,
        [string]$sshKey
    )

    $configContent = @()
    if (Test-Path -Path $configFile) {
        $configContent = Get-Content -Path $configFile
        $configContent = $configContent | Where-Object { $_ -notmatch "^ssh_key=" }
    }
    $configContent += "ssh_key=$sshKey"
    $configContent += ""
    $configContent | Set-Content -Path $configFile
    Write-Output "SSH key saved to .webwright_config file."
}

# Check if .webwright_config file exists and contains a valid SSH key path
$configFile = ".webwright_config"
if (Test-Path -Path $configFile) {
    $configContent = Get-Content -Path $configFile
    foreach ($line in $configContent) {
        if ($line -match "^ssh_key=(.+)$") {
            $selectedKey = $Matches[1]
            if (-not (Test-Path -Path $selectedKey)) {
                $selectedKey = $null
            }
            break
        }
    }
}

# If .webwright_config file doesn't exist or contains an invalid path, prompt user to select an SSH key
if (-not $selectedKey) {
    List-SSHKeys
    $selectedKey = Select-SSHKey
    
    # Save the selected SSH key path to the .webwright_config file
    Update-WebrightConfigSSHKey -configFile $configFile -sshKey $selectedKey
}

Write-Output "Selected SSH key: $selectedKey"
Configure-SSH -selectedKey $selectedKey

# Ensure remote URL is using SSH
git remote set-url origin git@github.com:mittaai/webwright.git

Write-Output "Conda environment '$envName' is now active and Git is configured with the selected SSH key."

# Keep the prompt open
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
