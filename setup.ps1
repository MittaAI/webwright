# setup.ps1
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

# Function to prompt for the OpenAI API key
function Get-OpenAIAPIKey {
    $openAIApiKey = $null
    while ([string]::IsNullOrWhiteSpace($openAIApiKey)) {
        $openAIApiKey = Read-Host "Please enter your OpenAI API key"
    }
    return $openAIApiKey
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

# Check if .ssh_key file exists and contains a valid SSH key path
$sshKeyFile = ".ssh_key"
if (Test-Path -Path $sshKeyFile) {
    $selectedKey = Get-Content -Path $sshKeyFile -First 1
    if (-not (Test-Path -Path $selectedKey)) {
        $selectedKey = $null
    }
}

# If .ssh_key file doesn't exist or contains an invalid path, prompt user to select an SSH key
if (-not $selectedKey) {
    List-SSHKeys
    $selectedKey = Select-SSHKey
    Set-Content -Path $sshKeyFile -Value $selectedKey
}

Write-Output "Selected SSH key: $selectedKey"
Configure-SSH -selectedKey $selectedKey

# Ensure remote URL is using SSH
git remote set-url origin git@github.com:mittaai/webwright.git

# Check if .openai_token file exists and read the OpenAI API key from it
$openAITokenFile = ".openai_token"
if (Test-Path -Path $openAITokenFile) {
    $env:OPENAI_API_KEY = Get-Content -Path $openAITokenFile -First 1
}

# If .openai_token file doesn't exist or is empty, prompt for the OpenAI API key and save it
if (-not $env:OPENAI_API_KEY) {
    $env:OPENAI_API_KEY = Get-OpenAIAPIKey
    Set-Content -Path $openAITokenFile -Value $env:OPENAI_API_KEY
}

Write-Output "Conda environment '$envName' is now active and Git is configured with the selected SSH key."

# Keep the prompt open
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")