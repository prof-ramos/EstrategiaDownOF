#!/bin/bash

# Enable strict mode:
# -e: exit on error
# -u: exit on undefined variables
# -o pipefail: catch errors in pipelines
set -euo pipefail

echo "🚀 Estratégia Downloader - Setup & Run"
echo "======================================"
echo

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    # Download installer to a temporary file for safety
    INSTALL_SCRIPT=$(mktemp)
    if ! curl -LsSf https://astral.sh/uv/install.sh -o "$INSTALL_SCRIPT"; then
        echo "❌ Error: Failed to download uv installer." >&2
        rm -f "$INSTALL_SCRIPT"
        exit 1
    fi

    # Run the installer
    sh "$INSTALL_SCRIPT"
    rm -f "$INSTALL_SCRIPT"

    # Update PATH for the current session
    # Note: uv usually installs to $HOME/.cargo/bin
    export PATH="$HOME/.cargo/bin:$PATH"

    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo "❌ Error: uv installation failed or is not in PATH." >&2
        exit 1
    fi
fi

echo "✓ uv installed/available"
echo

# Create virtual environment with uv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment with uv..."
    uv venv
    echo "✓ Virtual environment created"
fi

echo

# Install dependencies with uv if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📥 Installing dependencies with uv..."
    if ! uv pip install -r requirements.txt; then
        echo "❌ Error: Failed to install dependencies." >&2
        exit 1
    fi
    echo "✓ Dependencies installed"
else
    echo "❌ Error: requirements.txt not found." >&2
    exit 1
fi

echo

# Run the app
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found." >&2
    exit 1
fi

echo "▶️  Starting the application..."
echo
uv run python main.py "$@"
