"""
Integration tests for Motor ID cycling
Tests realistic motor ID changing scenarios
"""

import pytest
import time
from unittest.mock import Mock


class MockMotorWithHistory:
    """Enhanced mock motor that tracks command history"""
    def __init__(self, initial_id=1):
        self.current_id = initial_id
        self.is_connected = True
        self.commands_executed = []
        self.feedback_requests = []
    
    def set_motor_id(self, old_id: int, new_id: int) -> bool:
        """Simulate setting motor ID with history tracking"""
        self.commands_executed.append(f"set_motor_id({old_id}, {new_id})")
        
        if old_id == self.current_id:
            self.current_id = new_id
            return True
        else:
            return False
    
    def request_feedback(self, motor_id: int):
        """Simulate feedback request with history"""
        self.feedback_requests.append(motor_id)
        
        if motor_id == self.current_id:
            feedback = Mock()
            feedback.velocity = 100.0 + motor_id  # Different values per motor
            feedback.position = 45.0 + motor_id
            feedback.torque = 1.5
            feedback.temperature = 25 + motor_id
            return feedback
        else:
            return None


@pytest.fixture
def enhanced_mock_motor():
    """Create enhanced mock motor for cycling tests"""
    return MockMotorWithHistory()


@pytest.fixture  
def queue_with_enhanced_mock(enhanced_mock_motor):
    """Create queue with enhanced mock motor"""
    from motor_command_queue import MotorCommandQueue
    
    queue = MotorCommandQueue("/dev/null")
    queue.motor = enhanced_mock_motor
    return queue


class TestMotorIDCycling:
    """Test motor ID cycling scenarios"""
    
    @pytest.mark.integration
    def test_basic_cycling_sequence(self, queue_with_enhanced_mock):
        """Test basic motor ID cycling: 1 → 2 → 3 → 1"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        sequence = [(1, 2), (2, 3), (3, 1)]
        
        for old_id, new_id in sequence:
            # Verify starting state
            assert motor.current_id == old_id
            
            # Execute change
            result = queue.set_motor_id(old_id, new_id)
            
            # Verify success
            assert result is True
            assert motor.current_id == new_id
            
            # Simulate confirmation by requesting feedback
            feedback = motor.request_feedback(new_id)
            assert feedback is not None
            assert feedback.velocity == 100.0 + new_id
    
    @pytest.mark.integration
    def test_extended_cycling_sequence(self, queue_with_enhanced_mock):
        """Test extended cycling: 1 → 2 → 3 → 34 → 1 → 2"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        sequence = [(1, 2), (2, 3), (3, 34), (34, 1), (1, 2)]
        
        success_count = 0
        for i, (old_id, new_id) in enumerate(sequence):
            # Add realistic timing delay
            if i > 0:
                time.sleep(0.01)
            
            # Verify we're at expected starting point
            if motor.current_id != old_id:
                pytest.fail(f"Expected motor at ID {old_id}, but found {motor.current_id}")
            
            # Execute change
            result = queue.set_motor_id(old_id, new_id)
            
            if result:
                success_count += 1
                assert motor.current_id == new_id
                
                # Verify motor responds to new ID
                feedback = motor.request_feedback(new_id)
                assert feedback is not None
                
                # Verify motor doesn't respond to old ID
                old_feedback = motor.request_feedback(old_id)
                assert old_feedback is None
        
        # All changes should succeed
        assert success_count == len(sequence)
        
        # Verify command history
        assert len(motor.commands_executed) == len(sequence)
    
    @pytest.mark.integration
    def test_rapid_cycling(self, queue_with_enhanced_mock):
        """Test rapid motor ID cycling"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        # Rapid sequence: 1 → 2 → 1 → 2 → 1
        sequence = [(1, 2), (2, 1), (1, 2), (2, 1), (1, 2)]
        
        start_time = time.time()
        
        for old_id, new_id in sequence:
            result = queue.set_motor_id(old_id, new_id)
            assert result is True
            assert motor.current_id == new_id
        
        end_time = time.time()
        
        # Should complete quickly
        assert (end_time - start_time) < 0.1
        
        # Final motor should be at ID 2
        assert motor.current_id == 2
    
    @pytest.mark.integration
    def test_cycling_with_verification_steps(self, queue_with_enhanced_mock):
        """Test cycling with verification steps like real usage"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        sequence = [(1, 3), (3, 7), (7, 1)]
        
        for old_id, new_id in sequence:
            # Step 1: Verify current state
            initial_feedback = motor.request_feedback(old_id)
            assert initial_feedback is not None, f"Motor should respond to current ID {old_id}"
            
            # Step 2: Execute ID change
            result = queue.set_motor_id(old_id, new_id)
            assert result is True, f"Failed to change ID from {old_id} to {new_id}"
            
            # Step 3: Wait (simulate real timing)
            time.sleep(0.05)
            
            # Step 4: Verify new ID works
            new_feedback = motor.request_feedback(new_id)
            assert new_feedback is not None, f"Motor should respond to new ID {new_id}"
            
            # Step 5: Verify old ID no longer works
            old_feedback = motor.request_feedback(old_id)
            assert old_feedback is None, f"Motor should not respond to old ID {old_id}"
        
        # Verify complete command history
        expected_commands = [f"set_motor_id({old}, {new})" for old, new in sequence]
        assert motor.commands_executed == expected_commands


class TestMotorIDCyclingErrorScenarios:
    """Test error scenarios during cycling"""
    
    @pytest.mark.integration
    def test_cycling_with_invalid_intermediate_id(self, queue_with_enhanced_mock):
        """Test cycling where intermediate ID change fails"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        # Start with successful change
        result1 = queue.set_motor_id(1, 2)
        assert result1 is True
        assert motor.current_id == 2
        
        # Try invalid change (wrong current ID)
        result2 = queue.set_motor_id(99, 3)  # Wrong current ID
        assert result2 is False
        assert motor.current_id == 2  # Should remain unchanged
        
        # Continue with correct ID
        result3 = queue.set_motor_id(2, 3)
        assert result3 is True
        assert motor.current_id == 3
    
    @pytest.mark.integration
    def test_cycling_recovery_after_failure(self, queue_with_enhanced_mock):
        """Test that cycling can recover after failures"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        successful_changes = 0
        failed_changes = 0
        
        # Mix of valid and invalid changes
        test_sequence = [
            (1, 2, True),   # Should succeed
            (99, 3, False), # Should fail (wrong current ID)
            (2, 4, True),   # Should succeed  
            (1, 5, False),  # Should fail (wrong current ID)
            (4, 1, True),   # Should succeed
        ]
        
        for old_id, new_id, should_succeed in test_sequence:
            result = queue.set_motor_id(old_id, new_id)
            
            if should_succeed:
                assert result is True
                successful_changes += 1
                assert motor.current_id == new_id
            else:
                assert result is False
                failed_changes += 1
                # Motor ID should remain unchanged
        
        assert successful_changes == 3
        assert failed_changes == 2
        assert motor.current_id == 1  # Final state


class TestMotorIDCyclingPerformance:
    """Test performance aspects of motor ID cycling"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_sequence_cycling(self, queue_with_enhanced_mock):
        """Test cycling through a large sequence of IDs"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        # Create sequence: 1 → 2 → 3 → ... → 10 → 1
        ids = list(range(1, 11)) + [1]  # 1 through 10, then back to 1
        sequence = [(ids[i], ids[i+1]) for i in range(len(ids)-1)]
        
        start_time = time.time()
        
        success_count = 0
        for old_id, new_id in sequence:
            result = queue.set_motor_id(old_id, new_id)
            if result:
                success_count += 1
        
        end_time = time.time()
        
        # All should succeed
        assert success_count == len(sequence)
        
        # Should complete in reasonable time (adjust as needed)
        assert (end_time - start_time) < 1.0
        
        # Should end up back at ID 1
        assert motor.current_id == 1
        
        # Should have executed correct number of commands
        assert len(motor.commands_executed) == len(sequence)
    
    @pytest.mark.integration
    def test_cycling_memory_usage(self, queue_with_enhanced_mock):
        """Test that cycling doesn't cause memory leaks"""
        queue = queue_with_enhanced_mock
        motor = queue.motor
        
        # Cycle many times between two IDs
        cycles = 100
        for i in range(cycles):
            if i % 2 == 0:
                result = queue.set_motor_id(1, 2)
                assert result is True
            else:
                result = queue.set_motor_id(2, 1)
                assert result is True
        
        # History should contain all commands
        assert len(motor.commands_executed) == cycles
        
        # Memory usage verification would need more sophisticated tools
        # For now, just verify the objects are still functional
        assert motor.current_id in [1, 2]
        assert queue.is_connected