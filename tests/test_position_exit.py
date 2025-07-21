#!/usr/bin/env python3
"""
Test specifically exiting position mode
"""

import time
from ddsm115 import DDSM115, MotorMode

def get_mode_name(mode_val):
    return {1: "Current", 2: "Velocity", 3: "Position"}.get(mode_val, f"Unknown({mode_val})")

def test_position_exit():
    """Test exiting position mode reliably"""
    print("🔧 Position Mode Exit Test")
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
        
        # Make sure we start in position mode
        print("\n1. Setting position mode...")
        motor.set_mode(motor_id, MotorMode.POSITION)
        time.sleep(0.5)
        
        feedback = motor.request_feedback(motor_id)
        if feedback and len(feedback.raw_data) > 1:
            mode = feedback.raw_data[1]
            print(f"Current mode: {get_mode_name(mode)} ({mode})")
            
            if mode != 3:
                print("❌ Not in position mode - test invalid")
                return False
        
        # Try multiple attempts to switch to velocity
        for attempt in range(5):
            print(f"\n{attempt+2}. Attempt {attempt+1} to switch to velocity...")
            
            # Stop motor first
            motor.set_velocity(motor_id, 0)
            time.sleep(0.1)
            
            # Try switching to velocity
            success = motor.set_mode(motor_id, MotorMode.VELOCITY)
            print(f"   Mode switch command sent: {success}")
            time.sleep(0.5)
            
            # Check result
            feedback = motor.request_feedback(motor_id)
            if feedback and len(feedback.raw_data) > 1:
                mode = feedback.raw_data[1]
                print(f"   Result: {get_mode_name(mode)} ({mode})")
                
                if mode == 2:
                    print("   ✅ Successfully switched to velocity!")
                    
                    # Test velocity command
                    print("   Testing velocity command...")
                    motor.set_velocity(motor_id, 20)
                    time.sleep(1)
                    
                    feedback = motor.request_feedback(motor_id)
                    if feedback:
                        print(f"   Velocity: {feedback.velocity:.1f} RPM")
                    
                    motor.set_velocity(motor_id, 0)
                    return True
                else:
                    print(f"   ❌ Still in {get_mode_name(mode)} mode")
        
        print("\n❌ Failed to exit position mode after 5 attempts")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        try:
            motor.set_velocity(motor_id, 0)
        except:
            pass
        motor.disconnect()
        print("\n🔌 Disconnected")

if __name__ == "__main__":
    test_position_exit()