#!/usr/bin/env python3
"""
Example command-line usage of DDSM115 library
"""

import time
import sys
from ddsm115 import DDSM115, MotorMode, MotorFeedback


def main():
    # Check if port provided
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    
    print(f"DDSM115 Motor Control CLI Example")
    print(f"Using port: {port}")
    print("-" * 40)
    
    # Create motor controller
    motor = DDSM115(port=port)
    
    # Connect
    print("Connecting...")
    if not motor.connect():
        print("Failed to connect!")
        return
    
    print("Connected successfully!")
    
    try:
        # Scan for motors
        print("\nScanning for motors...")
        found_motors = motor.scan_motors(1, 10)
        
        if not found_motors:
            print("No motors found!")
            return
            
        print(f"Found motors: {found_motors}")
        motor_id = found_motors[0]
        print(f"Using motor ID: {motor_id}")
        
        # Demo velocity control
        print("\n--- Velocity Control Demo ---")
        motor.set_velocity(motor_id, 50)
        print("Motor spinning at 50 RPM")
        
        for i in range(5):
            feedback = motor.request_feedback(motor_id)
            if feedback:
                print(f"  Pos: {feedback.position:6.1f}° | "
                      f"Vel: {feedback.velocity:6.1f} RPM | "
                      f"Current: {feedback.torque:5.2f}A | "
                      f"Temp: {feedback.temperature}°C")
            time.sleep(0.5)
        
        # Stop
        motor.set_velocity(motor_id, 0)
        print("Motor stopped")
        time.sleep(1)
        
        # Demo position control
        print("\n--- Position Control Demo ---")
        positions = [0, 90, 180, 270, 0]
        
        for pos in positions:
            print(f"Moving to {pos}°...")
            motor.set_position(motor_id, pos)
            
            # Wait for position
            for _ in range(20):
                feedback = motor.request_feedback(motor_id)
                if feedback:
                    current_pos = feedback.position
                    error = abs(current_pos - pos)
                    print(f"  Current: {current_pos:6.1f}° | Target: {pos}° | Error: {error:5.1f}°")
                    
                    if error < 2.0:  # Within 2 degrees
                        break
                        
                time.sleep(0.1)
        
        print("\nDemo complete!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        # Always stop motor before disconnecting
        print("Stopping motor...")
        motor.emergency_stop(motor_id)
        motor.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    main()