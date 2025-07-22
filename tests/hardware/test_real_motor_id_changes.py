"""
Hardware tests for actual motor ID changes via RS485
These tests require real DDSM115 motors connected to RS485
"""

import pytest
import time
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ddsm115 import DDSM115
from motor_command_queue import MotorCommandQueue


@pytest.fixture
def real_motor_connection():
    """Connect to real motor hardware"""
    # Try common RS485 ports
    ports_to_try = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyAMA0", "/dev/serial0"]
    
    motor = None
    connected_port = None
    
    for port in ports_to_try:
        try:
            test_motor = DDSM115(port)
            if test_motor.connect():
                # Test if we can scan for motors
                motors = test_motor.scan_motors()
                if motors:
                    motor = test_motor
                    connected_port = port
                    break
                else:
                    test_motor.disconnect()
        except Exception as e:
            print(f"Failed to connect to {port}: {e}")
            continue
    
    if motor is None:
        pytest.skip("No motor hardware found on any port")
    
    print(f"Connected to motor hardware on {connected_port}")
    yield motor, connected_port
    
    # Cleanup
    if motor:
        motor.disconnect()


@pytest.fixture
def motor_queue_hardware(real_motor_connection):
    """Create MotorCommandQueue with real hardware"""
    motor, port = real_motor_connection
    queue = MotorCommandQueue(port)
    queue.motor = motor
    return queue


class TestRealMotorIDChanges:
    """Test actual motor ID changes with real hardware"""
    
    @pytest.mark.hardware
    def test_scan_for_motors(self, real_motor_connection):
        """Test scanning for motors on the bus"""
        motor, port = real_motor_connection
        
        print(f"Scanning for motors on {port}...")
        motors = motor.scan_motors()
        
        assert isinstance(motors, list)
        assert len(motors) > 0, "No motors found on bus"
        
        print(f"Found motors with IDs: {motors}")
        
        # Verify we can communicate with each found motor
        for motor_id in motors:
            feedback = motor.request_feedback(motor_id)
            assert feedback is not None, f"Cannot get feedback from motor {motor_id}"
            print(f"Motor {motor_id} - Temp: {feedback.temperature}°C, Pos: {feedback.position}°")
    
    @pytest.mark.hardware
    def test_real_motor_id_change_basic(self, motor_queue_hardware):
        """Test actual motor ID change: Find motor, change ID, verify"""
        queue = motor_queue_hardware
        motor = queue.motor
        
        # Step 1: Scan for existing motors
        initial_motors = motor.scan_motors()
        assert len(initial_motors) > 0, "No motors found for testing"
        
        current_id = initial_motors[0]  # Use first motor found
        print(f"Testing with motor ID {current_id}")
        
        # Step 2: Verify motor responds at current ID
        initial_feedback = motor.request_feedback(current_id)
        assert initial_feedback is not None, f"Motor {current_id} not responding"
        initial_temp = initial_feedback.temperature
        print(f"Initial state - Motor {current_id}: {initial_temp}°C")
        
        # Step 3: Choose target ID (must be 1-10, avoid conflicts)
        target_id = current_id + 1
        if target_id > 10:  # Motor only supports IDs 1-10
            target_id = current_id - 1
        if target_id < 1:
            target_id = current_id + 1
            
        print(f"Changing motor ID: {current_id} → {target_id}")
        
        # Step 4: Execute ID change
        success = queue.set_motor_id(current_id, target_id)
        assert success, f"Failed to change motor ID from {current_id} to {target_id}"
        
        # Step 5: Wait for change to take effect
        time.sleep(2.0)
        
        # Step 6: Verify motor no longer responds at old ID
        old_feedback = motor.request_feedback(current_id)
        assert old_feedback is None, f"Motor still responding at old ID {current_id}"
        
        # Step 7: Verify motor responds at new ID
        new_feedback = motor.request_feedback(target_id)
        assert new_feedback is not None, f"Motor not responding at new ID {target_id}"
        
        # Step 8: Verify it's the same motor (temperature should be similar)
        new_temp = new_feedback.temperature
        temp_diff = abs(new_temp - initial_temp)
        assert temp_diff < 5, f"Temperature changed too much: {initial_temp}°C → {new_temp}°C"
        
        print(f"SUCCESS: Motor ID changed {current_id} → {target_id}")
        print(f"New state - Motor {target_id}: {new_temp}°C")
        
        # Step 9: Change ID back to original
        print(f"Restoring original ID: {target_id} → {current_id}")
        restore_success = queue.set_motor_id(target_id, current_id)
        assert restore_success, f"Failed to restore motor ID to {current_id}"
        
        time.sleep(2.0)
        
        # Step 10: Verify restoration
        restored_feedback = motor.request_feedback(current_id)
        assert restored_feedback is not None, f"Motor not responding after ID restoration"
        print(f"Restored: Motor {current_id} responding normally")
    
    @pytest.mark.hardware
    def test_real_motor_id_cycling_sequence(self, motor_queue_hardware):
        """Test cycling through multiple real motor ID changes"""
        queue = motor_queue_hardware
        motor = queue.motor
        
        # Find available motor
        motors = motor.scan_motors()
        assert len(motors) > 0, "No motors found"
        
        start_id = motors[0]
        print(f"Starting motor ID cycling test with motor {start_id}")
        
        # Define test sequence (avoiding common IDs that might conflict)
        sequence = [
            (start_id, start_id + 20),
            (start_id + 20, start_id + 21), 
            (start_id + 21, start_id),  # Back to original
        ]
        
        for step, (old_id, new_id) in enumerate(sequence, 1):
            print(f"Step {step}: {old_id} → {new_id}")
            
            # Verify starting state
            feedback = motor.request_feedback(old_id)
            assert feedback is not None, f"Motor not at expected ID {old_id}"
            
            # Execute change
            success = queue.set_motor_id(old_id, new_id)
            assert success, f"Failed ID change {old_id} → {new_id}"
            
            # Wait for change
            time.sleep(1.5)
            
            # Verify new state
            new_feedback = motor.request_feedback(new_id)
            assert new_feedback is not None, f"Motor not responding at new ID {new_id}"
            
            # Verify old ID no longer works
            old_feedback = motor.request_feedback(old_id)
            assert old_feedback is None, f"Motor still responding at old ID {old_id}"
            
            print(f"Step {step} SUCCESS: Motor now at ID {new_id}")
        
        print("Motor ID cycling sequence completed successfully")
    
    @pytest.mark.hardware
    def test_motor_id_error_conditions(self, motor_queue_hardware):
        """Test error conditions with real hardware"""
        queue = motor_queue_hardware
        motor = queue.motor
        
        # Find available motor
        motors = motor.scan_motors()
        assert len(motors) > 0, "No motors found"
        
        current_id = motors[0]
        print(f"Testing error conditions with motor {current_id}")
        
        # Test 1: Wrong current ID should fail
        wrong_id = current_id + 50  # Assume this ID doesn't exist
        result = queue.set_motor_id(wrong_id, current_id + 1)
        assert result is False, "Should fail when using wrong current ID"
        print("✓ Correctly failed with wrong current ID")
        
        # Test 2: Verify motor still at original ID
        feedback = motor.request_feedback(current_id)
        assert feedback is not None, "Motor should still be at original ID"
        print(f"✓ Motor still correctly responds at ID {current_id}")
        
        # Test 3: Try to set ID to same value
        same_id_result = queue.set_motor_id(current_id, current_id)
        # This might succeed or fail depending on motor firmware
        print(f"Setting ID to same value returned: {same_id_result}")
        
        # Verify motor still responds
        feedback = motor.request_feedback(current_id)
        assert feedback is not None, "Motor should still respond after same-ID attempt"
        print("✓ Motor still responds after same-ID test")
    
    @pytest.mark.hardware  
    @pytest.mark.slow
    def test_motor_id_stress_test(self, motor_queue_hardware):
        """Stress test: rapid ID changes"""
        queue = motor_queue_hardware
        motor = queue.motor
        
        # Find available motor
        motors = motor.scan_motors()
        assert len(motors) > 0, "No motors found"
        
        base_id = motors[0]
        print(f"Starting stress test with motor {base_id}")
        
        # Rapid alternating sequence
        test_ids = [base_id, base_id + 30, base_id, base_id + 31, base_id]
        
        success_count = 0
        start_time = time.time()
        
        for i in range(len(test_ids) - 1):
            old_id = test_ids[i]
            new_id = test_ids[i + 1]
            
            print(f"Change {i+1}: {old_id} → {new_id}")
            
            success = queue.set_motor_id(old_id, new_id)
            if success:
                success_count += 1
                time.sleep(1.0)  # Give motor time to process
                
                # Verify change
                feedback = motor.request_feedback(new_id)
                if feedback is None:
                    print(f"WARNING: Motor not responding at new ID {new_id}")
                    break
            else:
                print(f"FAILED: Could not change {old_id} → {new_id}")
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Stress test completed: {success_count}/{len(test_ids)-1} changes in {duration:.1f}s")
        
        # Should have at least some successes
        assert success_count >= len(test_ids) // 2, "Too many failures in stress test"
        
        # Verify final state
        final_feedback = motor.request_feedback(base_id)
        assert final_feedback is not None, "Motor should be back at original ID"
        print(f"✓ Motor restored to original ID {base_id}")


class TestMotorIDWithGUIIntegration:
    """Test motor ID functionality as used by the GUI"""
    
    @pytest.mark.hardware
    def test_gui_workflow_simulation(self, motor_queue_hardware):
        """Simulate the exact workflow the GUI uses"""
        queue = motor_queue_hardware
        motor = queue.motor
        
        # Step 1: GUI would scan for motors
        motors = motor.scan_motors()
        assert len(motors) > 0, "No motors found"
        
        current_motor_id = motors[0]
        print(f"GUI workflow test with motor {current_motor_id}")
        
        # Step 2: GUI gets current ID from user dialog (simulate user input)
        user_entered_current_id = current_motor_id  # User enters this in dialog
        target_id = current_motor_id + 15  # GUI gets this from spinbox
        
        print(f"Simulating GUI: User entered current ID {user_entered_current_id}, target ID {target_id}")
        
        # Step 3: GUI calls set_motor_id
        callback_results = []
        
        def gui_callback(result):
            callback_results.append(result)
            print(f"GUI callback received: {result}")
        
        success = queue.set_motor_id(user_entered_current_id, target_id, callback=gui_callback)
        
        # Step 4: Verify callback was called
        assert len(callback_results) == 1, "Callback should be called once"
        assert callback_results[0] == success, "Callback should receive same result"
        assert success, f"Motor ID change should succeed"
        
        # Step 5: Wait like GUI would
        time.sleep(2.0)
        
        # Step 6: GUI might scan again to verify
        new_motors = motor.scan_motors()
        assert target_id in new_motors, f"New motor ID {target_id} should appear in scan"
        assert current_motor_id not in new_motors, f"Old motor ID {current_motor_id} should not appear in scan"
        
        print("GUI workflow simulation completed successfully")
        
        # Cleanup: restore original ID
        restore_success = queue.set_motor_id(target_id, current_motor_id)
        assert restore_success, "Should be able to restore original ID"
        time.sleep(1.0)
        
        final_motors = motor.scan_motors()
        assert current_motor_id in final_motors, "Original ID should be restored"
        print("✓ Original motor ID restored")