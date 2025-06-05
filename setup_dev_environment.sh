#!/bin/bash

# Setup script for development environment

echo "Setting up development environment for Bangladesh Student Data Analytics..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 isort mkdocs mkdocs-material pre-commit

# Initialize pre-commit
echo "Setting up pre-commit hooks..."
cat > .pre-commit-config.yaml << 'EOF'
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: debug-statements

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black
        language_version: python3

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-docstrings]
EOF

# Initialize pre-commit
pre-commit install

# Create initial test database
echo "Setting up test database..."
mkdir -p tests/data
touch tests/data/.gitkeep

# Setup documentation development
echo "Setting up documentation development environment..."
mkdir -p docs/assets/images
mkdir -p docs/assets/css

# Create example configuration
echo "Creating example configuration..."
if [ ! -f config/example.yaml ]; then
    cp config/example.yaml config/development.yaml
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please update .env with your local configuration values."
fi

# Final instructions
echo "
Development environment setup complete!

To start developing:
1. Activate the virtual environment:
   source venv/bin/activate

2. Update .env with your local configuration

3. Run tests:
   pytest

4. Start documentation server:
   mkdocs serve

5. Format code:
   black .
   isort .

For more information, refer to the documentation in docs/
"

# Make the script executable
chmod +x setup_dev_environment.sh
