#!/usr/bin/env python3
"""
Test slider responsiveness by monitoring the actual commands sent vs slider movements
"""

import time
import sys
from ddsm115 import DDSM115, MotorMode

class SliderResponsivenessTest:
    def __init__(self):
        self.motor = DDSM115(port="/dev/ttyUSB0", suppress_comm_errors=False)
        self.motor_id = None
        
    def connect_and_find_motor(self):
        """Connect and find motor"""
        if not self.motor.connect():
            print("❌ Failed to connect to motor")
            return False
        
        motors = self.motor.scan_motors(1, 10)
        if not motors:
            print("❌ No motors found")
            return False
        
        self.motor_id = motors[0]
        print(f"✅ Found motor at ID {self.motor_id}")
        return True
    
    def test_rapid_commands(self):
        """Test sending rapid commands like a user moving sliders quickly"""
        print("\n🚀 Testing Rapid Command Responsiveness")
        print("=" * 50)
        
        if not self.connect_and_find_motor():
            return
        
        # Test 1: Rapid velocity changes (simulating slider drag)
        print("\n1. Testing rapid velocity changes (simulating slider drag)...")
        
        # Switch to velocity mode first
        self.motor.set_mode(self.motor_id, MotorMode.VELOCITY)
        time.sleep(0.1)
        
        velocities = [0, 10, 20, 30, 40, 30, 20, 10, 0, -10, -20, -10, 0]
        command_times = []
        
        for i, vel in enumerate(velocities):
            start_time = time.time()
            success = self.motor.set_velocity(self.motor_id, vel)
            command_time = time.time() - start_time
            command_times.append(command_time)
            
            # Get feedback immediately
            feedback = self.motor.request_feedback(self.motor_id)
            actual_vel = feedback.velocity if feedback else "No feedback"
            
            print(f"   Command {i+1}: {vel:3d} RPM -> {command_time:.3f}s -> Actual: {actual_vel}")
            
            # Very short delay (simulating rapid slider movement)
            time.sleep(0.05)
        
        avg_time = sum(command_times) / len(command_times)
        max_time = max(command_times)
        
        print(f"\n   📊 Velocity Commands: {avg_time:.3f}s avg, {max_time:.3f}s max")
        
        if max_time > 0.1:
            print("   ⚠️ Slow commands detected - this could cause GUI lag")
        else:
            print("   ✅ Command speed looks good")
        
        # Test 2: Mode switching during rapid changes
        print("\n2. Testing mode switching during rapid changes...")
        
        # Rapid mode switches with commands
        test_sequence = [
            (MotorMode.VELOCITY, 25, "set_velocity"),
            (MotorMode.CURRENT, 1.0, "set_current"),
            (MotorMode.VELOCITY, -15, "set_velocity"),
            (MotorMode.CURRENT, -0.5, "set_current"),
            (MotorMode.VELOCITY, 0, "set_velocity")
        ]
        
        switch_times = []
        
        for i, (mode, value, command_method) in enumerate(test_sequence):
            start_time = time.time()
            
            # Switch mode
            self.motor.set_mode(self.motor_id, mode)
            time.sleep(0.05)  # Small delay for mode switch
            
            # Send command
            method = getattr(self.motor, command_method)
            method(self.motor_id, value)
            
            total_time = time.time() - start_time
            switch_times.append(total_time)
            
            # Get feedback
            feedback = self.motor.request_feedback(self.motor_id)
            mode_name = {1: "Current", 2: "Velocity", 3: "Position"}.get(feedback.raw_data[1] if feedback and len(feedback.raw_data) > 1 else 0, "Unknown")
            
            print(f"   Switch {i+1}: {mode.name} {value} -> {total_time:.3f}s -> Mode: {mode_name}")
            
            time.sleep(0.1)
        
        avg_switch_time = sum(switch_times) / len(switch_times)
        max_switch_time = max(switch_times)
        
        print(f"\n   📊 Mode Switches: {avg_switch_time:.3f}s avg, {max_switch_time:.3f}s max")
        
        if max_switch_time > 0.2:
            print("   ⚠️ Slow mode switching - this could cause GUI delays")
        else:
            print("   ✅ Mode switching speed looks good")
    
    def test_position_mode_transition(self):
        """Test the specific position mode transition with velocity ramping"""
        print("\n📍 Testing Position Mode Transition")
        print("=" * 40)
        
        if not self.motor_id:
            return
        
        # Start with motor spinning
        print("1. Starting motor at 50 RPM...")
        self.motor.set_mode(self.motor_id, MotorMode.VELOCITY)
        time.sleep(0.1)
        self.motor.set_velocity(self.motor_id, 50)
        time.sleep(1)
        
        # Check velocity
        feedback = self.motor.request_feedback(self.motor_id)
        if feedback:
            print(f"   Current velocity: {feedback.velocity:.1f} RPM")
        
        # Now try to switch to position mode (should trigger ramping)
        print("2. Attempting position mode switch (should trigger velocity ramping)...")
        
        start_time = time.time()
        
        # This simulates what the GUI should do
        # Step 1: Check velocity
        feedback = self.motor.request_feedback(self.motor_id)
        if feedback and abs(feedback.velocity) >= 10:
            print(f"   Velocity {feedback.velocity:.1f} RPM >= 10, need to ramp down")
            
            # Step 2: Ramp down (simulate GUI ramping)
            ramp_steps = []
            current_vel = feedback.velocity
            
            while abs(current_vel) >= 10:
                # Reduce by 20% or minimum 10 RPM
                vel_reduction = max(abs(current_vel) * 0.2, 10)
                if current_vel > 0:
                    next_vel = max(0, current_vel - vel_reduction)
                else:
                    next_vel = min(0, current_vel + vel_reduction)
                
                print(f"   Ramping: {current_vel:.1f} -> {next_vel:.1f} RPM")
                self.motor.set_velocity(self.motor_id, int(next_vel))
                ramp_steps.append(next_vel)
                
                time.sleep(0.1)  # Wait for motor to respond
                
                feedback = self.motor.request_feedback(self.motor_id)
                current_vel = feedback.velocity if feedback else 0
                
                # Safety check to prevent infinite loop
                if len(ramp_steps) > 20:
                    print("   ⚠️ Ramp taking too long, stopping")
                    break
            
            print(f"   ✅ Ramped down in {len(ramp_steps)} steps")
        
        # Step 3: Switch to position mode
        print("3. Switching to position mode...")
        position_switch_success = self.motor.set_mode(self.motor_id, MotorMode.POSITION)
        time.sleep(0.1)
        
        # Verify
        feedback = self.motor.request_feedback(self.motor_id)
        if feedback and len(feedback.raw_data) > 1:
            actual_mode = feedback.raw_data[1]
            if actual_mode == 3:
                print("   ✅ Successfully switched to position mode")
            else:
                print(f"   ❌ Mode switch failed, still in mode {actual_mode}")
        
        total_time = time.time() - start_time
        print(f"   📊 Total transition time: {total_time:.3f}s")
        
        if total_time > 2.0:
            print("   ⚠️ Slow transition - users might experience delays")
        else:
            print("   ✅ Transition speed acceptable")
    
    def test_feedback_consistency(self):
        """Test if feedback is consistent and timely"""
        print("\n📡 Testing Feedback Consistency")
        print("=" * 35)
        
        if not self.motor_id:
            return
        
        print("Testing 50 consecutive feedback requests...")
        
        response_times = []
        failed_requests = 0
        
        for i in range(50):
            start_time = time.time()
            feedback = self.motor.request_feedback(self.motor_id)
            response_time = time.time() - start_time
            
            if feedback:
                response_times.append(response_time)
                if i % 10 == 0:
                    print(f"   Request {i+1}: {response_time:.3f}s")
            else:
                failed_requests += 1
                print(f"   Request {i+1}: FAILED")
            
            time.sleep(0.02)  # 50Hz rate
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\n   📊 Feedback Stats:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Range: {min_time:.3f}s - {max_time:.3f}s")
            print(f"   Failed: {failed_requests}/50")
            
            if avg_time > 0.05:
                print("   ⚠️ Slow feedback - this could cause GUI updates to lag")
            elif failed_requests > 2:
                print("   ⚠️ Unreliable feedback - GUI might miss updates")
            else:
                print("   ✅ Feedback performance looks good")
        
        self.motor.disconnect()

def main():
    print("🔧 DDSM115 Slider Responsiveness Test")
    print("This test simulates rapid slider movements to identify GUI lag sources")
    
    tester = SliderResponsivenessTest()
    
    tester.test_rapid_commands()
    tester.test_position_mode_transition()
    tester.test_feedback_consistency()
    
    print("\n✅ Testing complete!")
    print("\nThis data helps identify:")
    print("- Command latency that could cause slider lag")
    print("- Mode switching delays")
    print("- Feedback timing issues affecting graph updates")

if __name__ == "__main__":
    main()