#!/bin/bash
# Simple setup script for DDSM115 Motor Control
# Creates a portable installation that can be moved between hosts

echo "🔧 DDSM115 Motor Control - Portable Setup"
echo "========================================"

# Create portable directory structure
INSTALL_DIR="ddsm115-portable"
echo "📁 Creating portable installation in $INSTALL_DIR..."

mkdir -p "$INSTALL_DIR"

# Copy all necessary files
cp ddsm115_gui.py "$INSTALL_DIR/"
cp ddsm115.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp README.md "$INSTALL_DIR/"
cp install.sh "$INSTALL_DIR/"

# Copy example files if they exist
[ -f example_cli.py ] && cp example_cli.py "$INSTALL_DIR/"
[ -f motor_diagnostic.py ] && cp motor_diagnostic.py "$INSTALL_DIR/"

# Create a virtual environment in the portable directory
echo "🔧 Creating virtual environment..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Create launcher scripts
echo "📝 Creating launcher scripts..."

# Linux/Mac launcher
cat > start.sh << 'EOF'
#!/bin/bash
# DDSM115 Motor Control Launcher
cd "$(dirname "$0")"
source venv/bin/activate
python3 ddsm115_gui.py
EOF
chmod +x start.sh

# Windows launcher
cat > start.bat << 'EOF'
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python ddsm115_gui.py
pause
EOF

# Cross-platform Python launcher
cat > start.py << 'EOF'
#!/usr/bin/env python3
"""Cross-platform launcher for DDSM115 Motor Control"""
import os
import sys
import subprocess
import platform

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Determine platform and activate virtual environment
if platform.system() == "Windows":
    venv_python = os.path.join("venv", "Scripts", "python.exe")
else:
    venv_python = os.path.join("venv", "bin", "python")

# Check if virtual environment exists
if not os.path.exists(venv_python):
    print("❌ Virtual environment not found!")
    print("Please run install.sh first to set up the environment.")
    sys.exit(1)

# Launch the GUI application
try:
    subprocess.run([venv_python, "ddsm115_gui.py"])
except KeyboardInterrupt:
    print("\n👋 Application closed by user")
except Exception as e:
    print(f"❌ Error launching application: {e}")
    sys.exit(1)
EOF
chmod +x start.py

# Create README for portable installation
cat > PORTABLE_README.md << 'EOF'
# DDSM115 Motor Control - Portable Installation

This is a self-contained, portable installation that can be moved between computers.

## Quick Start

### Linux/Mac:
```bash
./start.sh
```

### Windows:
Double-click `start.bat`

### Cross-platform:
```bash
python3 start.py
```

## Moving to Another Computer

1. Copy this entire folder to the new computer
2. Make sure Python 3.8+ is installed on the target computer
3. Run the appropriate start script for your platform
4. If there are issues, you can reinstall dependencies:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate.bat  # Windows
   
   pip install -r requirements.txt
   ```

## Troubleshooting

- **Permission errors**: Make sure scripts are executable (`chmod +x start.sh`)
- **Python not found**: Ensure Python 3.8+ is installed and in PATH
- **Virtual environment issues**: Delete `venv` folder and run `install.sh`

EOF

echo ""
echo "✅ Portable installation created successfully!"
echo ""
echo "📁 Installation location: $(pwd)"
echo ""
echo "🚀 To start the application:"
echo "   Linux/Mac: ./start.sh"
echo "   Windows:   start.bat"
echo "   Python:    python3 start.py"
echo ""
echo "📦 To move to another computer:"
echo "   1. Copy the entire '$INSTALL_DIR' folder"
echo "   2. Run the appropriate start script"
echo ""
echo "💡 See PORTABLE_README.md for more details"