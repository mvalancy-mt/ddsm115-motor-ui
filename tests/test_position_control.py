#!/usr/bin/env python3
"""
Test DDSM115 position control directly
"""

import time
from ddsm115 import DDSM115, MotorMode

def test_position_control():
    """Test position control step by step"""
    print("🔧 DDSM115 Position Control Test")
    print("=" * 40)
    
    motor = DDSM115(port="/dev/ttyUSB0", suppress_comm_errors=False)
    
    try:
        # Connect
        print("1. Connecting...")
        if not motor.connect():
            print("❌ Failed to connect")
            return False
        print("✅ Connected")
        
        # Find motor
        print("\n2. Scanning for motors...")
        found_motors = motor.scan_motors(1, 10)
        if not found_motors:
            print("❌ No motors found")
            return False
        
        motor_id = found_motors[0]
        print(f"✅ Found motor at ID {motor_id}")
        
        # Get initial feedback
        print(f"\n3. Reading initial status...")
        feedback = motor.request_feedback(motor_id)
        if feedback:
            print(f"   Initial Position: {feedback.position:.1f}°")
            print(f"   Initial Velocity: {feedback.velocity:.1f} RPM")
            # Check current mode from raw data
            if len(feedback.raw_data) > 1:
                mode_val = feedback.raw_data[1]
                mode_name = {1: "Current", 2: "Velocity", 3: "Position"}.get(mode_val, f"Unknown({mode_val})")
                print(f"   Current Mode: {mode_name} ({mode_val})")
        
        # Stop motor first
        print(f"\n4. Stopping motor...")
        motor.set_velocity(motor_id, 0)
        time.sleep(1)
        
        # Switch to position mode explicitly
        print(f"\n5. Setting position mode...")
        if motor.set_mode(motor_id, MotorMode.POSITION):
            print("✅ Position mode command sent")
            time.sleep(0.5)  # Wait for mode switch
            
            # Verify mode change
            feedback = motor.request_feedback(motor_id)
            if feedback and len(feedback.raw_data) > 1:
                mode_val = feedback.raw_data[1]
                mode_name = {1: "Current", 2: "Velocity", 3: "Position"}.get(mode_val, f"Unknown({mode_val})")
                print(f"   Mode after switch: {mode_name} ({mode_val})")
                
                if mode_val == 3:
                    print("✅ Successfully switched to position mode")
                else:
                    print("❌ Mode switch failed - still in wrong mode")
            
        else:
            print("❌ Failed to send position mode command")
            return False
        
        # Test position commands
        test_positions = [90, 180, 270, 0]
        print(f"\n6. Testing position commands...")
        
        for target_pos in test_positions:
            print(f"\n   Setting position to {target_pos}°...")
            if motor.set_position(motor_id, target_pos):
                print(f"   ✅ Position command sent")
                
                # Wait and check position
                time.sleep(2)
                feedback = motor.request_feedback(motor_id)
                if feedback:
                    print(f"   Target: {target_pos}°, Actual: {feedback.position:.1f}°")
                    print(f"   Velocity: {feedback.velocity:.1f} RPM")
                    
                    # Check if position actually changed
                    if abs(feedback.position - target_pos) < 10:  # Within 10 degrees
                        print(f"   ✅ Position reached!")
                    else:
                        print(f"   ❌ Position not reached (off by {abs(feedback.position - target_pos):.1f}°)")
                else:
                    print(f"   ❌ No feedback")
            else:
                print(f"   ❌ Position command failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        motor.disconnect()
        print("\n🔌 Disconnected")

if __name__ == "__main__":
    test_position_control()