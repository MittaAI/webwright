#!/bin/bash

# setup.sh
pythonVersion="3.8"
requirementsFile="requirements.txt"

# Get the name of the root directory (checked out project path name)
projectPath=$(pwd)
envName=$(basename "$projectPath")

# Function to check if a conda environment exists
test_conda_env_exists() {
    envs=$(conda env list | grep -w "$envName")
    [ -n "$envs" ]
}

# Function to create a new conda environment
create_conda_env() {
    echo "Creating new conda environment: $envName"
    conda create -y --name "$envName" python="$pythonVersion"
}

echo "Activating conda environment: $envName"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$envName"

# Function to install requirements
install_requirements() {
    echo "Installing packages from $requirementsFile"
    conda run -n "$envName" pip install -r "$requirementsFile"
}

# Function to install Git using Conda
install_git() {
    echo "Git is not installed. Installing Git..."
    conda install -y -n "$envName" -c anaconda git
}

# Function to list SSH keys
list_ssh_keys() {
    sshDirectory="$HOME/.ssh"
    if [ ! -d "$sshDirectory" ]; then
        echo "No .ssh directory found in $HOME" >&2
        exit 1
    fi
    keys=$(find "$sshDirectory" -type f -name "id*" ! -name "*.pub")
    if [ -z "$keys" ]; then
        echo "No SSH keys found in $sshDirectory" >&2
        exit 1
    fi
    echo "Available SSH keys:"
    i=0
    while read -r key; do
        echo "$i: $(basename "$key")"
        ((i++))
    done <<< "$keys"
}

# Function to prompt user to select an SSH key
select_ssh_key() {
    sshDirectory="$HOME/.ssh"
    keys=$(find "$sshDirectory" -type f -name "id*" ! -name "*.pub")
    read -p "Enter the number of the SSH key to use: " selection
    if ! [[ $selection =~ ^[0-9]+$ ]] || [ "$selection" -ge "$(wc -l <<< "$keys")" ]; then
        echo "Invalid selection" >&2
        exit 1
    fi
    selectedKey=$(sed -n "$((selection + 1))p" <<< "$keys")
    echo "$selectedKey"
}

# Function to configure SSH for the selected key
configure_ssh() {
    selectedKey="$1"
    sshConfigFile="$HOME/.ssh/config"
    touch "$sshConfigFile"
    cat > "$sshConfigFile" <<EOL
Host github.com
  HostName github.com
  User git
  IdentityFile $selectedKey
  IdentitiesOnly yes
EOL
    echo "SSH configuration updated."

    # Set the global core.sshCommand to use the selected key
    git config --global core.sshCommand "ssh -i $selectedKey"
    echo "Global SSH command configuration updated."
}

# Function to prompt for the OpenAI API key
get_openai_api_key() {
    read -p "Please enter your OpenAI API key: " openAIApiKey
    while [ -z "$openAIApiKey" ]; do
        read -p "Please enter your OpenAI API key: " openAIApiKey
    done
    echo "$openAIApiKey"
}


# Function to prompt for the Anthropic API key
get_anthropic_api_key() {
    read -p "Please enter your Anthropic API key: " anthropicApiKey
    while [ -z "$anthropicApiKey" ]; do
        read -p "Anthropic API key cannot be empty. Please enter your Anthropic API key: " anthropicApiKey
    done
    echo "$anthropicApiKey"
}


# Main script
if ! command -v conda &> /dev/null; then
    echo "Conda is not installed or not found in the system PATH." >&2
    exit 1
fi

if test_conda_env_exists; then
    echo "Conda environment '$envName' already exists."
else
    create_conda_env
fi

echo "Activating conda environment: $envName"
conda activate "$envName"

# Check if Git is installed
if ! command -v git &> /dev/null; then
    install_git
else
    echo "Git is already installed."
fi

if [ -f "$requirementsFile" ]; then
    install_requirements
else
    echo "Requirements file '$requirementsFile' not found. Skipping package installation."
fi

update_shell_config() {
    shellConfigFile="$HOME/.bashrc"  # Change to the appropriate shell configuration file if needed
    openAIApiKey="$1"

    if [ -f "$shellConfigFile" ]; then
        sed -i.bak '/^export OPENAI_API_KEY=/d' "$shellConfigFile"
    fi
    echo "export OPENAI_API_KEY=$openAIApiKey" >> "$shellConfigFile"
    echo "OpenAI API key added to $shellConfigFile"
}

# Function to update the .webwright_config file with the SSH key
update_webright_config_sshkey() {
    configFile="$1"
    sshKey="$2"

    if [ -f "$configFile" ]; then
        sed -i.bak '/^ssh_key=/d' "$configFile"
    fi
    echo "ssh_key=$sshKey" >> "$configFile"
    echo "" >> "$configFile"
    echo "SSH key saved to .webwright_config file."
}

# Check if .webwright_config file exists and contains a valid SSH key path
configFile=".webwright_config"
if [ -f "$configFile" ]; then
    selectedKey=$(grep '^ssh_key=' "$configFile" | cut -d'=' -f2-)
    if [ ! -f "$selectedKey" ]; then
        selectedKey=""
    fi
fi

# If .webwright_config file doesn't exist or contains an invalid path, prompt user to select an SSH key
if [ -z "$selectedKey" ]; then
    list_ssh_keys
    selectedKey=$(select_ssh_key)
    
    # Save the selected SSH key path to the .webwright_config file
    update_webright_config_sshkey "$configFile" "$selectedKey"
fi

echo "Selected SSH key: $selectedKey"
configure_ssh "$selectedKey"

# Ensure remote URL is using SSH
git remote set-url origin git@github.com:mittaai/webwright.git

echo "Conda environment '$envName' is now active and Git is configured with the selected SSH key."

# Function to update the .webwright_config file with the OpenAI API key
update_webright_config_openai() {
    configFile="$1"
    openAIApiKey="$2"

    if [ -f "$configFile" ]; then
        sed -i.bak '/^openai_key=/d' "$configFile"
    fi
    echo "openai_key=$openAIApiKey" >> "$configFile"
    echo "" >> "$configFile"
    echo "OpenAI API key saved to .webwright_config file."
}

# Check if .webwright_config file exists and contains a valid OpenAI API key
openAIApiKey=""
if [ -f "$configFile" ]; then
    openAIApiKey=$(grep '^openai_key=' "$configFile" | cut -d'=' -f2-)
fi

# If OpenAI API key is not found in the .webwright_config file or is empty,
# check if the environment variable is set
if [ -z "$openAIApiKey" ]; then
    if [ -n "$OPENAI_API_KEY" ]; then
        openAIApiKey="$OPENAI_API_KEY"
        # Save the API key from the environment variable to the .webwright_config file
        update_webright_config_openai "$configFile" "$openAIApiKey"
    else
        # If the environment variable is not set, prompt for the key and save it to the file
        openAIApiKey=$(get_openai_api_key)
        update_webright_config_openai "$configFile" "$openAIApiKey"
    fi
fi

# Set the OpenAI API key as an environment variable if it's not already set
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="$openAIApiKey"
fi

# Function to update the .webwright_config file with the Anthropic API key
update_webright_config_anthropic() {
    configFile="$1"
    anthropicApiKey="$2"

    if [ -f "$configFile" ]; then
        sed -i.bak '/^anthropic_key=/d' "$configFile"
    fi
    echo "anthropic_key=$anthropicApiKey" >> "$configFile"
    echo "" >> "$configFile"
    echo "Anthropic API key saved to .webwright_config file."
}

# Check if .webwright_config file exists and contains a valid Anthropic API key
anthropicApiKey=""
if [ -f "$configFile" ]; then
    anthropicApiKey=$(grep '^anthropic_key=' "$configFile" | cut -d'=' -f2-)
fi

# If Anthropic API key is not found in the .webwright_config file or is empty,
# check if the environment variable is set
if [ -z "$anthropicApiKey" ]; then
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        anthropicApiKey="$ANTHROPIC_API_KEY"
        # Save the API key from the environment variable to the .webwright_config file
        update_webright_config_anthropic "$configFile" "$anthropicApiKey"
    else
        # If the environment variable is not set, prompt for the key and save it to the file
        anthropicApiKey=$(get_anthropic_api_key)
        update_webright_config_anthropic "$configFile" "$anthropicApiKey"
    fi
fi

# Set the Anthropic API key as an environment variable if it's not already set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    export ANTHROPIC_API_KEY="$anthropicApiKey"
fi

# Keep the script running until a key is pressed
read -n1 -s -r -p "Press any key to continue..."