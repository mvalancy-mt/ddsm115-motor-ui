"""
Unit tests for Motor ID functionality
Tests the set_motor_id feature without requiring hardware
"""

import pytest
import time
from unittest.mock import Mock, patch


class TestMotorIDBasicFunctionality:
    """Test basic motor ID functionality"""
    
    @pytest.mark.unit
    def test_motor_command_queue_has_set_motor_id_method(self):
        """Test that MotorCommandQueue has set_motor_id method"""
        from motor_command_queue import MotorCommandQueue
        
        queue = MotorCommandQueue("/dev/null")
        assert hasattr(queue, 'set_motor_id')
        assert callable(queue.set_motor_id)
    
    @pytest.mark.unit
    def test_ddsm115_has_set_motor_id_method(self):
        """Test that DDSM115 class has set_motor_id method"""
        from ddsm115 import DDSM115
        
        assert hasattr(DDSM115, 'set_motor_id')
        assert callable(DDSM115.set_motor_id)
    
    @pytest.mark.unit
    def test_set_motor_id_method_signature(self):
        """Test set_motor_id method has correct signature"""
        from motor_command_queue import MotorCommandQueue
        import inspect
        
        queue = MotorCommandQueue("/dev/null")
        sig = inspect.signature(queue.set_motor_id)
        
        # Should have old_id, new_id, and optional callback parameters
        params = list(sig.parameters.keys())
        assert 'old_id' in params
        assert 'new_id' in params
        assert 'callback' in params
        
        # Check return type annotation
        assert sig.return_annotation == bool
    
    @pytest.mark.unit
    def test_set_motor_id_disconnected_returns_false(self, disconnected_motor_command_queue):
        """Test that set_motor_id returns False when disconnected"""
        result = disconnected_motor_command_queue.set_motor_id(1, 2)
        assert result is False
    
    @pytest.mark.unit
    def test_set_motor_id_connected_calls_underlying_motor(self, mock_motor_command_queue):
        """Test that set_motor_id calls the underlying motor method"""
        result = mock_motor_command_queue.set_motor_id(1, 2)
        
        assert result is True
        assert mock_motor_command_queue.motor.current_id == 2
        assert len(mock_motor_command_queue.motor.commands_executed) == 1


class TestMotorIDSequencing:
    """Test motor ID changing sequences"""
    
    @pytest.mark.unit
    def test_basic_id_sequence(self, mock_motor_command_queue, sample_motor_ids):
        """Test basic motor ID sequence changes"""
        queue = mock_motor_command_queue
        sequence = sample_motor_ids['basic_sequence']
        
        success_count = 0
        for old_id, new_id in sequence:
            result = queue.set_motor_id(old_id, new_id)
            if result:
                success_count += 1
                assert queue.motor.current_id == new_id
        
        assert success_count == len(sequence)
    
    @pytest.mark.unit  
    def test_extended_id_sequence(self, mock_motor_command_queue, sample_motor_ids):
        """Test extended motor ID sequence with larger IDs"""
        queue = mock_motor_command_queue
        sequence = sample_motor_ids['extended_sequence']
        
        success_count = 0
        for old_id, new_id in sequence:
            # Ensure we start from the expected state
            if queue.motor.current_id != old_id:
                # Skip this test case or adjust
                continue
                
            result = queue.set_motor_id(old_id, new_id)
            if result:
                success_count += 1
                assert queue.motor.current_id == new_id
            
        assert success_count > 0  # At least some should succeed
    
    @pytest.mark.unit
    def test_id_sequence_with_timing(self, mock_motor_command_queue):
        """Test motor ID changes with realistic timing"""
        queue = mock_motor_command_queue
        
        # Test sequence: 1 → 2 → 3 → 1
        sequence = [(1, 2), (2, 3), (3, 1)]
        
        for old_id, new_id in sequence:
            start_time = time.time()
            result = queue.set_motor_id(old_id, new_id)
            end_time = time.time()
            
            assert result is True
            assert queue.motor.current_id == new_id
            
            # Should complete quickly (within 100ms for mock)
            assert (end_time - start_time) < 0.1
            
            # Add small delay like real usage
            time.sleep(0.01)


class TestMotorIDErrorCases:
    """Test motor ID error handling"""
    
    @pytest.mark.unit
    def test_wrong_current_id_returns_false(self, mock_motor_command_queue):
        """Test that wrong current ID returns False"""
        queue = mock_motor_command_queue
        
        # Motor is at ID 1, try to change from ID 99
        result = queue.set_motor_id(99, 2)
        assert result is False
        assert queue.motor.current_id == 1  # Unchanged
    
    @pytest.mark.unit
    def test_same_id_change(self, mock_motor_command_queue):
        """Test changing to same ID"""
        queue = mock_motor_command_queue
        
        # Try to change ID 1 to ID 1
        result = queue.set_motor_id(1, 1)
        # This might succeed or fail depending on implementation
        # Just verify it doesn't crash
        assert isinstance(result, bool)
    
    @pytest.mark.unit
    def test_callback_on_success(self, mock_motor_command_queue):
        """Test that callback is called on success"""
        callback_called = []
        
        def test_callback(result):
            callback_called.append(result)
        
        result = mock_motor_command_queue.set_motor_id(1, 2, callback=test_callback)
        
        assert result is True
        assert len(callback_called) == 1
        assert callback_called[0] is True
    
    @pytest.mark.unit
    def test_callback_on_failure(self, mock_motor_command_queue):
        """Test that callback is called on failure"""
        callback_called = []
        
        def test_callback(result):
            callback_called.append(result)
        
        # Use wrong current ID to force failure
        result = mock_motor_command_queue.set_motor_id(99, 2, callback=test_callback)
        
        assert result is False
        assert len(callback_called) == 1
        assert callback_called[0] is False


class TestMotorIDIntegration:
    """Integration tests for motor ID functionality"""
    
    @pytest.mark.integration
    def test_gui_set_motor_id_method_exists(self):
        """Test that GUI has set_motor_id method"""
        # Import GUI code to check method exists
        import os
        gui_file = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'ddsm115_gui.py')
        
        with open(gui_file, 'r') as f:
            content = f.read()
        
        assert 'def set_motor_id(self):' in content
        assert 'motor_controller.set_motor_id(' in content
    
    @pytest.mark.integration 
    def test_gui_uses_simpledialog(self):
        """Test that GUI imports and uses simpledialog"""
        import os
        gui_file = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'ddsm115_gui.py')
        
        with open(gui_file, 'r') as f:
            content = f.read()
        
        assert 'simpledialog' in content
        assert 'askinteger' in content
    
    @pytest.mark.integration
    def test_complete_workflow_simulation(self, mock_motor_command_queue):
        """Test complete workflow simulation"""
        queue = mock_motor_command_queue
        
        # Simulate the complete workflow that GUI would do:
        # 1. Check connection
        # 2. Get current and target IDs  
        # 3. Call set_motor_id
        # 4. Verify result
        
        # Step 1: Check connection (mock is always connected)
        assert queue.is_connected
        
        # Step 2: Simulate GUI getting IDs
        current_id = 1  # What user enters in dialog
        target_id = 2   # What's in the spinbox
        
        # Step 3: Call set_motor_id
        result = queue.set_motor_id(current_id, target_id)
        
        # Step 4: Verify
        assert result is True
        assert queue.motor.current_id == target_id
        
        # Step 5: Verify motor responds to new ID
        feedback = queue.motor.request_feedback(target_id)
        assert feedback is not None
        
        # Step 6: Verify motor doesn't respond to old ID  
        old_feedback = queue.motor.request_feedback(current_id)
        assert old_feedback is None