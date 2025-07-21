#!/bin/bash
# DDSM115 Motor Control GUI - Easy Installation Script
# Works on Linux, macOS, and Windows (with Git Bash/WSL)

echo "🚀 DDSM115 Motor Control GUI Installer"
echo "======================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ first:"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-pip python3-tk"
    echo "  - macOS: brew install python3-tk"
    echo "  - Windows: Download from python.org"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed"
    echo "Please install pip first:"
    echo "  - Ubuntu/Debian: sudo apt install python3-pip"
    echo "  - macOS/Windows: Usually included with Python"
    exit 1
fi

echo "✅ pip found"

# Option for virtual environment
echo ""
echo "📦 Installation Options:"
echo "1. Install globally (system packages)"
echo "2. Create virtual environment (recommended)"
echo ""
read -p "Choose option (1 or 2): " install_option

if [ "$install_option" = "2" ]; then
    echo "🔧 Creating virtual environment..."
    
    # Create virtual environment
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
    
    # Install all requirements in venv
    echo "📦 Installing requirements in virtual environment..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ All requirements installed successfully in venv"
        echo ""
        echo "🎯 To use this installation:"
        echo "   source venv/bin/activate"
        echo "   python3 ddsm115_gui.py"
        echo ""
        echo "📝 Creating activation script..."
        cat > run.sh << 'EOF'
#!/bin/bash
# DDSM115 Motor Control - Easy Runner
cd "$(dirname "$0")"
source venv/bin/activate
python3 ddsm115_gui.py
EOF
        chmod +x run.sh
        echo "✅ Created run.sh - just execute ./run.sh to start the app!"
    else
        echo "❌ Failed to install requirements in virtual environment"
        exit 1
    fi
else
    # Global installation
    echo "📦 Installing packages globally..."
    
    # Check if pyserial is already installed
    python3 -c "import serial" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ pyserial is already installed"
    else
        echo "📦 Installing pyserial..."
        
        # Try pip installation first
        if command -v pip3 &> /dev/null; then
            pip3 install --user pyserial
        else
            pip install --user pyserial
        fi
        
        # Verify pyserial
        python3 -c "import serial" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "⚠️  pip install failed, trying system package manager..."
            if command -v apt &> /dev/null; then
                echo "📦 Installing python3-serial via apt..."
                sudo apt update && sudo apt install -y python3-serial
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y python3-pyserial
            elif command -v pacman &> /dev/null; then
                sudo pacman -S --noconfirm python-pyserial
            elif command -v brew &> /dev/null; then
                pip3 install pyserial
            else
                echo "❌ Could not install pyserial automatically"
                exit 1
            fi
        fi
    fi
    
    # Check and install matplotlib (optional but recommended)
    python3 -c "import matplotlib" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ matplotlib is already installed"
    else
        echo "📊 Installing matplotlib for graph functionality..."
        if command -v pip3 &> /dev/null; then
            pip3 install --user matplotlib numpy
        else
            pip install --user matplotlib numpy
        fi
        
        # Verify matplotlib
        python3 -c "import matplotlib" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ matplotlib installed successfully"
        else
            echo "⚠️  matplotlib installation failed - graphs will use text mode"
        fi
    fi
fi

# Check if tkinter is available (Linux only issue)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    python3 -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️  tkinter not found"
        echo "Installing tkinter..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install python3-tk
        elif command -v yum &> /dev/null; then
            sudo yum install tkinter
        elif command -v pacman &> /dev/null; then
            sudo pacman -S tk
        else
            echo "Please install tkinter manually for your Linux distribution"
        fi
    fi
fi

echo ""
echo "🎉 Installation Complete!"
echo ""
if [ "$install_option" = "2" ]; then
    echo "📋 Next Steps (Virtual Environment):"
    echo "1. Connect your DDSM115 motor hardware"
    echo "2. Run: ./run.sh (or: source venv/bin/activate && python3 ddsm115_gui.py)"
    echo "3. Click 'Connect' and start controlling!"
else
    echo "📋 Next Steps (Global Installation):"
    echo "1. Connect your DDSM115 motor hardware"
    echo "2. Run the application: python3 ddsm115_gui.py"
    echo "3. Click 'Connect' and start controlling!"
fi
echo ""
echo "💡 Need help? Check README.md for troubleshooting"

# Make the GUI script executable
if [ -f "ddsm115_gui.py" ]; then
    chmod +x ddsm115_gui.py
    echo "✅ Made ddsm115_gui.py executable"
fi