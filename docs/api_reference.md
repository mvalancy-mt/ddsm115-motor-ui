# DDSM115 Motor Control API Reference

## Core Classes

### `MotorCommandQueue`
Main interface for motor control with robust command queuing.

```python
class MotorCommandQueue:
    def __init__(self, port: str = "/dev/ttyUSB0")
    
    # Connection Management
    def connect(self) -> bool
    def disconnect(self) -> None
    def is_connected(self) -> bool
    
    # Motor Control
    def set_velocity(self, motor_id: int, velocity: float, callback: Optional[Callable] = None)
    def set_position(self, motor_id: int, position: float, callback: Optional[Callable] = None)  
    def set_current(self, motor_id: int, current: float, callback: Optional[Callable] = None)
    def set_mode(self, motor_id: int, mode: MotorMode, callback: Optional[Callable] = None)
    
    # Safety
    def stop(self, motor_id: int, callback: Optional[Callable] = None)
    def enable(self, motor_id: int, callback: Optional[Callable] = None)
    def disable(self, motor_id: int, callback: Optional[Callable] = None)
    
    # Monitoring
    def request_feedback(self, motor_id: int, callback: Optional[Callable] = None)
    def get_last_feedback(self, motor_id: int) -> Optional[MotorFeedback]
    def scan_motors(self, start_id: int = 1, end_id: int = 10) -> list
    
    # Statistics
    def get_stats(self) -> dict
```

### Communication Protocol

#### Command Packet Format
All motor commands use 10-byte packets:

```
Byte 0:    Motor ID (1-10)
Byte 1:    Command Type
Bytes 2-8: Command Data (6 bytes)
Byte 9:    Mode/Value
```

#### Command Types
```python
class CommandType(Enum):
    MODE_SWITCH = 0xA0    # Switch control mode
    SET_VELOCITY = 0xA1   # Set velocity command
    SET_POSITION = 0xA2   # Set position command  
    SET_CURRENT = 0xA3    # Set current command
    REQUEST_STATUS = 0xA4 # Request feedback
    ENABLE = 0xA5         # Enable motor
    DISABLE = 0xA6        # Disable motor
```

## Usage Examples

### Basic Motor Control
```python
from motor_command_queue import MotorCommandQueue

# Initialize controller
controller = MotorCommandQueue("/dev/ttyUSB0")

# Connect and find motors
if controller.connect():
    motors = controller.scan_motors()
    if motors:
        motor_id = motors[0]
        
        # Set velocity
        controller.set_velocity(motor_id, 50)  # 50 RPM
        
        # Set position  
        controller.set_position(motor_id, 180)  # 180 degrees
        
        # Set current
        controller.set_current(motor_id, 2.0)   # 2 Amps
        
        # Emergency stop
        controller.stop(motor_id)
        
    controller.disconnect()
```

### Feedback Monitoring
```python
def on_feedback(motor_id, feedback):
    print(f"Motor {motor_id}:")
    print(f"  Velocity: {feedback.velocity} RPM")
    print(f"  Position: {feedback.position}°")
    print(f"  Torque: {feedback.torque} A")

# Setup callback
controller.on_feedback = on_feedback

# Manual feedback request
feedback = controller.request_feedback(motor_id)
if feedback:
    print(f"Current position: {feedback.position}°")
```

### Error Handling
```python
def on_error(error_msg):
    print(f"Motor Error: {error_msg}")

controller.on_error = on_error

# Get statistics
stats = controller.get_stats()
print(f"Commands processed: {stats['commands_processed']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

This API provides both high-level convenience and low-level control
for comprehensive DDSM115 motor management.