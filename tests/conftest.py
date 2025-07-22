"""
Shared pytest fixtures for DDSM115 Motor Control tests
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_motor():
    """Create a mock DDSM115 motor for testing"""
    mock = Mock()
    mock.is_connected = True
    mock.current_id = 1
    mock.commands_executed = []
    
    def mock_set_motor_id(old_id, new_id):
        if old_id == mock.current_id:
            mock.current_id = new_id
            mock.commands_executed.append(f"ID changed: {old_id} → {new_id}")
            return True
        return False
    
    def mock_request_feedback(motor_id):
        if motor_id == mock.current_id:
            feedback_mock = Mock()
            feedback_mock.velocity = 100.0
            feedback_mock.position = 45.0
            feedback_mock.torque = 1.5
            feedback_mock.temperature = 25
            feedback_mock.raw_data = [motor_id, 2, 0, 0, 0, 0, 25, 45, 0, 0]
            return feedback_mock
        return None
    
    mock.set_motor_id = mock_set_motor_id
    mock.request_feedback = mock_request_feedback
    mock.connect = Mock(return_value=True)
    mock.disconnect = Mock()
    mock.scan_motors = Mock(return_value=[1, 2])
    
    return mock

@pytest.fixture
def mock_motor_command_queue(mock_motor):
    """Create a mock MotorCommandQueue with injected mock motor"""
    from motor_command_queue import MotorCommandQueue
    
    queue = MotorCommandQueue("/dev/null")  
    queue.motor = mock_motor  # Inject our mock
    return queue

@pytest.fixture
def disconnected_motor_command_queue():
    """Create a MotorCommandQueue that simulates disconnected state"""
    from motor_command_queue import MotorCommandQueue
    
    queue = MotorCommandQueue("/dev/null")
    # Don't set motor or set it to None to simulate disconnection
    queue.motor = None
    return queue

@pytest.fixture
def sample_motor_ids():
    """Provide sample motor ID sequences for testing"""
    return {
        'basic_sequence': [(1, 2), (2, 3), (3, 1)],
        'extended_sequence': [(1, 2), (2, 3), (3, 34), (34, 1), (1, 2)],
        'edge_cases': [(1, 1), (0, 1), (1, 255), (255, 1)],
        'invalid_sequences': [(99, 1), (1, -1), (-1, 1)]
    }