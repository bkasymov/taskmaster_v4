#!/bin/bash

# Set up environment variables
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Install pyenv dependencies
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Reload shell
exec $SHELL

# Install Python 3.11.7
pyenv install 3.11.7

# Set Python 3.11.7 as the global version
pyenv global 3.11.7

# Verify Python version
python --version

# Install pipenv
pip install --user pipenv

# Add pipenv to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify pipenv installation
pipenv --version

echo "Python 3.11.7 and pipenv have been installed successfully!"
