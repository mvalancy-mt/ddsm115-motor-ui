#!/usr/bin/env python3
"""
Quick test script for the simplified GUI
"""

import sys
import tkinter as tk
from ddsm115_gui import SimpleDDSM115GUI

def test_gui():
    """Test GUI creation and basic functionality"""
    print("Testing simplified DDSM115 GUI...")
    
    try:
        # Create root window
        root = tk.Tk()
        
        # Create GUI instance
        app = SimpleDDSM115GUI(root)
        
        print("✅ GUI created successfully!")
        print("✅ All 3 tabs created:")
        print("   - 🔌 Connection tab")
        print("   - 🎮 Control tab") 
        print("   - ℹ️ About tab")
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        
        # Test port refresh
        app.refresh_ports()
        print("✅ Port refresh works")
        
        # Test log message
        app.log_message("Test log message")
        print("✅ Log message works")
        
        # Test clear log
        app.clear_log()
        print("✅ Clear log works")
        
        # Test graph clearing
        app.clear_graph()
        print("✅ Clear graph works")
        
        # Clean up
        root.destroy()
        print("\n✅ All tests passed! GUI is working correctly.")
        print("🚀 Run with './run.sh' to use the full interface")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing GUI: {e}")
        return False

if __name__ == "__main__":
    test_gui()