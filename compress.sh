#!/bin/bash

# Enable strict mode:
# -e: exit on error
# -u: exit on undefined variables
# -o pipefail: catch errors in pipelines
set -euo pipefail

echo "🎬 Estratégia Downloader - Video Compressor"
echo "==========================================="
echo

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ Error: FFmpeg not found!" >&2
    echo "Install with: brew install ffmpeg" >&2
    exit 1
fi

echo "✓ FFmpeg available"
echo

# Check if uv is available, otherwise use Python directly
if command -v uv &> /dev/null; then
    # Create virtual environment with uv if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "🔧 Creating virtual environment with uv..."
        uv venv
        echo "✓ Virtual environment created"
    fi

    # Install dependencies with uv if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        echo "📥 Installing dependencies with uv..."
        if ! uv pip install -r requirements.txt; then
            echo "❌ Error: Failed to install dependencies." >&2
            exit 1
        fi
        echo "✓ Dependencies installed"
    fi

    echo
    echo "▶️  Starting compression..."
    echo
    uv run python compress_videos.py "$@"
else
    # Fallback to direct Python
    echo "⚠ uv not found, using Python directly..."

    # Create venv if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "🔧 Creating virtual environment..."
        python3 -m venv .venv
        echo "✓ Virtual environment created"
    fi

    # Activate venv
    source .venv/bin/activate

    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        echo "📥 Installing dependencies..."
        if ! python3 -m pip install -r requirements.txt --quiet; then
            echo "❌ Error: Failed to install dependencies." >&2
            exit 1
        fi
        echo "✓ Dependencies installed"
    fi

    echo
    echo "▶️  Starting compression..."
    echo
    python3 compress_videos.py "$@"
fi
