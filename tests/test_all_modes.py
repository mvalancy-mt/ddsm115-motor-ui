#!/usr/bin/env python3
"""
Test all DDSM115 control modes independently
"""

import time
from ddsm115 import DDSM115, MotorMode

def get_mode_name(mode_val):
    return {1: "Current", 2: "Velocity", 3: "Position"}.get(mode_val, f"Unknown({mode_val})")

def test_all_modes():
    """Test switching between all control modes"""
    print("🔧 DDSM115 All Modes Test")
    print("=" * 50)
    
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
        
        # Test each mode
        modes_to_test = [
            (MotorMode.VELOCITY, "Velocity", 2),
            (MotorMode.CURRENT, "Current", 1), 
            (MotorMode.POSITION, "Position", 3),
            (MotorMode.VELOCITY, "Velocity", 2)  # Test switching back
        ]
        
        for i, (mode_enum, mode_name, expected_val) in enumerate(modes_to_test, 1):
            print(f"\n{i+2}. Testing {mode_name} Mode")
            print("-" * 30)
            
            # Try to reset motor before mode switch if not already in target mode
            feedback = motor.request_feedback(motor_id)
            if feedback and len(feedback.raw_data) > 1:
                current_mode = feedback.raw_data[1]
                if current_mode != expected_val:
                    print(f"   Current mode: {get_mode_name(current_mode)} ({current_mode})")
                    print(f"   Stopping motor and disabling before mode switch...")
                    motor.set_velocity(motor_id, 0)  # Stop motor
                    time.sleep(0.2)
                    # Try disable/enable sequence
                    motor.disable(motor_id)
                    time.sleep(0.2)
                    motor.enable(motor_id)
                    time.sleep(0.2)
            
            # Set mode
            print(f"   Setting {mode_name} mode (value {expected_val})...")
            if motor.set_mode(motor_id, mode_enum):
                print(f"   ✅ {mode_name} mode command sent")
                time.sleep(0.5)  # Wait longer for mode switch
                
                # Try multiple readings to see if mode changes
                for attempt in range(3):
                    time.sleep(0.2)
                    temp_feedback = motor.request_feedback(motor_id)
                    if temp_feedback and len(temp_feedback.raw_data) > 1:
                        temp_mode = temp_feedback.raw_data[1]
                        print(f"   Attempt {attempt+1}: Mode = {get_mode_name(temp_mode)} ({temp_mode})")
                        if temp_mode == expected_val:
                            break
                
                # Verify mode change
                feedback = motor.request_feedback(motor_id)
                if feedback and len(feedback.raw_data) > 1:
                    actual_mode = feedback.raw_data[1]
                    actual_name = get_mode_name(actual_mode)
                    print(f"   Mode verification: {actual_name} ({actual_mode})")
                    
                    if actual_mode == expected_val:
                        print(f"   ✅ Successfully switched to {mode_name} mode")
                        
                        # Test command in this mode
                        if mode_enum == MotorMode.VELOCITY:
                            print(f"   Testing velocity command (30 RPM)...")
                            if motor.set_velocity(motor_id, 30):
                                time.sleep(1)
                                feedback = motor.request_feedback(motor_id)
                                if feedback:
                                    print(f"   Result: {feedback.velocity:.1f} RPM")
                                    # Stop motor
                                    motor.set_velocity(motor_id, 0)
                                    
                        elif mode_enum == MotorMode.CURRENT:
                            print(f"   Testing current command (1.0 A)...")
                            if motor.set_current(motor_id, 1.0):
                                time.sleep(1)
                                feedback = motor.request_feedback(motor_id)
                                if feedback:
                                    print(f"   Result: {feedback.torque:.2f} A")
                                    # Stop motor
                                    motor.set_current(motor_id, 0)
                                    
                        elif mode_enum == MotorMode.POSITION:
                            # Get current position first
                            feedback = motor.request_feedback(motor_id)
                            if feedback:
                                current_pos = feedback.position
                                target_pos = (current_pos + 45) % 360  # Move 45 degrees
                                print(f"   Testing position command ({target_pos:.1f}°)...")
                                if motor.set_position(motor_id, target_pos):
                                    time.sleep(2)
                                    feedback = motor.request_feedback(motor_id)
                                    if feedback:
                                        print(f"   Target: {target_pos:.1f}°, Actual: {feedback.position:.1f}°")
                        
                    else:
                        print(f"   ❌ Mode switch failed - expected {expected_val}, got {actual_mode}")
                else:
                    print(f"   ❌ No feedback after mode switch")
            else:
                print(f"   ❌ Failed to send {mode_name} mode command")
        
        print(f"\n🎉 Mode switching test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Stop motor and disconnect
        try:
            motor.set_velocity(motor_id, 0)
        except:
            pass
        motor.disconnect()
        print("\n🔌 Disconnected")

if __name__ == "__main__":
    test_all_modes()