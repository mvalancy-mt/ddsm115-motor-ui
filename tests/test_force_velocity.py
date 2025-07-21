#!/usr/bin/env python3
"""
Test if velocity commands can force mode switch from position mode
"""

import time
from ddsm115 import DDSM115, MotorMode

def get_mode_name(mode_val):
    return {1: "Current", 2: "Velocity", 3: "Position"}.get(mode_val, f"Unknown({mode_val})")

def test_force_velocity():
    """Test forcing velocity mode from position mode"""
    print("🔧 Force Velocity Mode Test")
    print("=" * 40)
    
    motor = DDSM115(port="/dev/ttyUSB0", suppress_comm_errors=False)
    
    try:
        if not motor.connect():
            print("❌ Failed to connect")
            return False
        
        found_motors = motor.scan_motors(1, 10)
        if not found_motors:
            print("❌ No motors found")
            return False
        
        motor_id = found_motors[0]
        print(f"✅ Found motor at ID {motor_id}")
        
        # Check current mode
        feedback = motor.request_feedback(motor_id)
        if feedback and len(feedback.raw_data) > 1:
            current_mode = feedback.raw_data[1]
            print(f"Current mode: {get_mode_name(current_mode)} ({current_mode})")
        
        # Try setting velocity mode via set_mode
        print("\n1. Trying set_mode to velocity...")
        motor.set_mode(motor_id, MotorMode.VELOCITY)
        time.sleep(0.5)
        
        feedback = motor.request_feedback(motor_id)
        if feedback and len(feedback.raw_data) > 1:
            mode_after = feedback.raw_data[1]
            print(f"Mode after set_mode: {get_mode_name(mode_after)} ({mode_after})")
        
        # Try sending velocity command directly (this calls set_velocity which forces velocity mode)
        print("\n2. Trying direct velocity command (30 RPM)...")
        if motor.set_velocity(motor_id, 30):
            print("✅ Velocity command sent")
            time.sleep(1)
            
            feedback = motor.request_feedback(motor_id)
            if feedback and len(feedback.raw_data) > 1:
                mode_after_vel = feedback.raw_data[1]
                print(f"Mode after velocity command: {get_mode_name(mode_after_vel)} ({mode_after_vel})")
                print(f"Actual velocity: {feedback.velocity:.1f} RPM")
                
                if mode_after_vel == 2:
                    print("✅ Successfully forced velocity mode!")
                else:
                    print("❌ Still not in velocity mode")
            
            # Stop motor
            motor.set_velocity(motor_id, 0)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        motor.disconnect()
        print("\n🔌 Disconnected")

if __name__ == "__main__":
    test_force_velocity()