#!/usr/bin/env python3
"""
Quick motor movement test script
Run this to test if motor can spin without the GUI
"""

import time
from ddsm115 import DDSM115, MotorMode

def test_motor_movement():
    """Test motor movement step by step"""
    print("🔧 DDSM115 Motor Movement Test")
    print("=" * 40)
    
    # Create motor controller
    motor = DDSM115(port="/dev/ttyUSB0", suppress_comm_errors=True)
    
    try:
        # Step 1: Connect
        print("1. Connecting to motor...")
        if not motor.connect():
            print("❌ Failed to connect to /dev/ttyUSB0")
            print("   Check that the motor is connected and powered")
            return False
        print("✅ Connected")
        
        # Step 2: Scan for motors
        print("\n2. Scanning for motors...")
        found_motors = motor.scan_motors(1, 10)
        if not found_motors:
            print("❌ No motors found")
            print("   Check motor power and RS485 connections")
            return False
        
        motor_id = found_motors[0]
        print(f"✅ Found motor at ID {motor_id}")
        
        # Step 3: Get initial status
        print(f"\n3. Reading initial status...")
        feedback = motor.request_feedback(motor_id)
        if feedback:
            print(f"   Velocity: {feedback.velocity:.1f} RPM")
            print(f"   Position: {feedback.position:.1f}°")
            print(f"   Torque: {feedback.torque:.2f} A")
            if feedback.temperature > 0:
                print(f"   Temperature: {feedback.temperature}°C")
        else:
            print("❌ No feedback received")
            return False
        
        # Step 4: Enable motor
        print(f"\n4. Enabling motor...")
        if not motor.enable(motor_id):
            print("❌ Failed to enable motor")
            return False
        print("✅ Motor enabled")
        time.sleep(0.5)
        
        # Step 5: Set velocity mode
        print(f"\n5. Setting velocity mode...")
        if not motor.set_mode(motor_id, MotorMode.VELOCITY):
            print("❌ Failed to set velocity mode")
            return False
        print("✅ Velocity mode set")
        time.sleep(0.5)
        
        # Step 6: Release brake
        print(f"\n6. Releasing brake...")
        motor.release_brake(motor_id)
        time.sleep(0.2)
        
        # Step 7: Test movement
        print(f"\n7. Testing movement (25 RPM for 3 seconds)...")
        if not motor.set_velocity(motor_id, 25):
            print("❌ Failed to set velocity")
            return False
        print("✅ Velocity command sent")
        
        # Monitor for 3 seconds
        for i in range(3):
            time.sleep(1)
            feedback = motor.request_feedback(motor_id)
            if feedback:
                print(f"   After {i+1}s: {feedback.velocity:.1f} RPM, {feedback.torque:.2f} A")
            else:
                print(f"   After {i+1}s: No feedback")
        
        # Step 8: Stop motor
        print(f"\n8. Stopping motor...")
        motor.set_velocity(motor_id, 0)
        time.sleep(0.5)
        
        # Final status
        feedback = motor.request_feedback(motor_id)
        if feedback:
            if abs(feedback.velocity) < 1:
                print("✅ Motor stopped successfully")
            else:
                print(f"⚠️ Motor still moving: {feedback.velocity:.1f} RPM")
        
        print(f"\n🎉 Motor test completed!")
        
        # Check if motor actually moved
        if feedback and abs(feedback.velocity) > 1:
            print("✅ Motor is capable of movement")
        else:
            print("⚠️ Motor may not have moved. Check:")
            print("   - Power supply voltage (12-24V)")
            print("   - Mechanical load or obstruction")
            print("   - Motor brake status")
            print("   - Wiring connections")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Always disconnect safely
        motor.disconnect()
        print("🔌 Disconnected")

if __name__ == "__main__":
    test_motor_movement()