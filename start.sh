#!/bin/bash
# DDSM115 Motor Control - Unified Launcher
# Handles first-time setup and launching

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎯 DDSM115 Motor Control - Starting..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    echo "📋 Please install Python 3.8+ and try again."
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   RHEL/CentOS:   sudo yum install python3 python3-pip"
    echo "   macOS:         brew install python"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 First-time setup: Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/.requirements_installed" ] || [ "requirements.txt" -nt "venv/.requirements_installed" ]; then
    echo "📦 Installing/updating requirements..."
    if [ -f "requirements.txt" ]; then
        ./venv/bin/pip install --upgrade pip
        ./venv/bin/pip install -r requirements.txt
        touch venv/.requirements_installed
    else
        echo "⚠️  requirements.txt not found, installing minimal dependencies..."
        ./venv/bin/pip install --upgrade pip
        ./venv/bin/pip install pyserial matplotlib numpy
        touch venv/.requirements_installed
    fi
fi

# Check if source files exist in the new structure
if [ -f "src/ddsm115_gui.py" ]; then
    echo "🚀 Launching DDSM115 Motor Control GUI..."
    cd src
    ../venv/bin/python3 ddsm115_gui.py
elif [ -f "ddsm115_gui.py" ]; then
    echo "🚀 Launching DDSM115 Motor Control GUI (legacy location)..."
    ./venv/bin/python3 ddsm115_gui.py
else
    echo "❌ Main application file not found!"
    echo "📋 Please ensure ddsm115_gui.py exists in the current directory or src/ directory."
    exit 1
fi