#!/usr/bin/env python3
"""
Test script for DDSM210 integration
Tests motor detection and basic functionality without GUI
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from motor_command_queue import MotorCommandQueue
from ddsm210 import DDSM210, scan_ports

def test_port_scanning():
    """Test port scanning functionality"""
    print("🔍 Testing port scanning...")
    ports = scan_ports()
    print(f"Available ports: {ports}")
    return ports

def test_ddsm210_direct():
    """Test DDSM210 class directly"""
    print("🔧 Testing DDSM210 class directly...")
    
    # Try common DDSM210 ports
    test_ports = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0", "/dev/ttyUSB1"]
    
    for port in test_ports:
        try:
            print(f"  Testing {port}...")
            motor = DDSM210(port=port, suppress_comm_errors=True)
            if motor.connect():
                print(f"  ✅ DDSM210 connected on {port}")
                
                # Test motor scan
                motors = motor.scan_motors()
                print(f"  Found motors: {motors}")
                
                motor.disconnect()
                return port
            else:
                print(f"  ❌ No connection on {port}")
        except Exception as e:
            print(f"  ❌ Error on {port}: {e}")
    
    print("  ⚠️ No DDSM210 motors found")
    return None

def test_motor_queue_auto_detection():
    """Test MotorCommandQueue auto-detection"""
    print("🤖 Testing MotorCommandQueue auto-detection...")
    
    available_ports = scan_ports()
    if not available_ports:
        print("  ⚠️ No serial ports available")
        return
    
    for port in available_ports[:3]:  # Test first 3 ports
        try:
            print(f"  Testing auto-detection on {port}...")
            queue = MotorCommandQueue(port=port, motor_type="auto")
            
            if queue.connect():
                motor_type = queue.get_motor_type()
                print(f"  ✅ Detected {motor_type.upper()} on {port}")
                
                queue.disconnect()
                return port, motor_type
            else:
                print(f"  ❌ No motor detected on {port}")
        except Exception as e:
            print(f"  ❌ Error testing {port}: {e}")
    
    print("  ⚠️ No motors detected via auto-detection")
    return None

def main():
    print("🧪 DDSM210 Integration Test")
    print("=" * 50)
    
    # Test 1: Port scanning
    ports = test_port_scanning()
    print()
    
    # Test 2: Direct DDSM210 connection
    ddsm210_port = test_ddsm210_direct()
    print()
    
    # Test 3: Auto-detection via MotorCommandQueue
    auto_result = test_motor_queue_auto_detection()
    print()
    
    # Summary
    print("📋 Test Summary:")
    print(f"  Available ports: {len(ports) if ports else 0}")
    print(f"  DDSM210 direct test: {'✅ SUCCESS' if ddsm210_port else '❌ FAILED'}")
    print(f"  Auto-detection test: {'✅ SUCCESS' if auto_result else '❌ FAILED'}")
    
    if auto_result:
        port, motor_type = auto_result
        print(f"  Detected motor: {motor_type.upper()} on {port}")
    
    print()
    if ddsm210_port or auto_result:
        print("✅ Integration test PASSED - Ready for GUI testing")
        print("   Run: python3 src/ddsm115_gui.py")
    else:
        print("⚠️ Integration test completed with warnings")
        print("   No motors detected - check connections and power")

if __name__ == "__main__":
    main()