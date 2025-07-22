# DDSM115 Motor Control - API Reference

## Table of Contents
1. [Core Classes](#core-classes)
2. [Motor Control](#motor-control)
3. [Data Management](#data-management)
4. [GUI Components](#gui-components)
5. [Protocol Implementation](#protocol-implementation)
6. [Testing Framework](#testing-framework)

---

## Core Classes

### DDSM115

The main motor control class implementing the DDSM115 RS485 protocol.

```python
class DDSM115:
    def __init__(self, port: str = "/dev/ttyUSB0", timeout: float = 0.2)
```

#### Methods

##### Connection Management
```python
def connect(self) -> bool:
    """Establish RS485 connection to motor controller."""

def disconnect(self) -> None:
    """Close RS485 connection and cleanup resources."""

def is_connected(self) -> bool:
    """Check if RS485 connection is active."""
```

##### Motor Control
```python
def set_velocity(self, motor_id: int, velocity: float) -> bool:
    """Set motor velocity in RPM (-330 to +330)."""

def set_position(self, motor_id: int, position: float) -> bool:
    """Set motor position in degrees (0 to 360)."""

def set_current(self, motor_id: int, current: float) -> bool:
    """Set motor current in Amps (-8 to +8)."""

def emergency_stop(self, motor_id: int) -> bool:
    """Immediately stop motor motion."""
```

##### Data Collection
```python
def request_feedback(self, motor_id: int) -> Optional[MotorFeedback]:
    """Request current motor status and sensor data."""

def scan_motors(self, start_id: int = 1, end_id: int = 10) -> List[int]:
    """Scan for active motors in ID range."""
```

##### Motor Configuration
```python
def set_motor_id(self, old_id: int, new_id: int) -> bool:
    """Change motor ID (requires power cycle for multiple changes)."""

def set_mode(self, motor_id: int, mode: str) -> bool:
    """Set motor control mode (velocity/position/current)."""
```

---

### MotorCommandQueue

Thread-safe motor command management with automatic feedback collection.

```python
class MotorCommandQueue:
    def __init__(self, port: str = "/dev/ttyUSB0")
```

#### Properties
```python
@property
def is_connected(self) -> bool:
    """Connection status (read-only)."""

@property  
def motor(self) -> Optional[DDSM115]:
    """Access to underlying DDSM115 instance."""
```

#### Callback Management
```python
on_feedback: Optional[Callable[[int, MotorFeedback], None]]
on_error: Optional[Callable[[str], None]]
on_command_sent: Optional[Callable[[str], None]]
```

#### Methods
```python
def connect(self, port: str = None) -> bool:
    """Connect to motor controller and start feedback worker."""

def disconnect(self) -> None:
    """Disconnect and stop all background threads."""

def set_velocity(self, motor_id: int, velocity: float) -> bool:
    """Queue velocity command for execution."""

def set_position(self, motor_id: int, position: float) -> bool:
    """Queue position command for execution."""

def set_current(self, motor_id: int, current: float) -> bool:
    """Queue current command for execution."""

def emergency_stop(self, motor_id: int) -> bool:
    """Immediate emergency stop (bypasses queue)."""

def set_motor_id(self, old_id: int, new_id: int, callback: Optional[Callable] = None) -> bool:
    """Change motor ID with optional completion callback."""
```

---

### MotorFeedback

Data container for motor sensor readings.

```python
@dataclass
class MotorFeedback:
    motor_id: int
    velocity: float      # RPM
    position: float      # Degrees  
    torque: float        # Amps
    temperature: int     # Celsius
    raw_data: List[int]  # Raw protocol bytes
    timestamp: float     # Unix timestamp
```

---

## Motor Control

### Control Modes

#### Velocity Mode
- **Range**: -330 to +330 RPM
- **Resolution**: 0.1 RPM
- **Use Case**: Continuous rotation applications

```python
# Set velocity
motor.set_velocity(motor_id=1, velocity=100.0)  # 100 RPM clockwise
motor.set_velocity(motor_id=1, velocity=-50.0)  # 50 RPM counter-clockwise
```

#### Position Mode  
- **Range**: 0 to 360 degrees
- **Resolution**: 0.1 degrees
- **Use Case**: Precise positioning

```python
# Set position
motor.set_position(motor_id=1, position=180.0)  # Move to 180 degrees
motor.set_position(motor_id=1, position=0.0)    # Return to zero position
```

#### Current Mode
- **Range**: -8 to +8 Amps
- **Resolution**: 0.01 Amps
- **Use Case**: Torque control

```python
# Set current (torque)
motor.set_current(motor_id=1, current=2.5)   # 2.5A clockwise torque
motor.set_current(motor_id=1, current=-1.0)  # 1.0A counter-clockwise torque
```

### Safety Commands

```python
# Emergency stop (immediate)
motor.emergency_stop(motor_id=1)

# Graceful stop (via velocity=0)
motor.set_velocity(motor_id=1, velocity=0.0)
```

### Protocol Implementation

#### Packet Format

DDSM115 uses 10-byte packets with CRC8 validation:

```python
# Command packet structure
[Header1, Header2, Command, Data0, Data1, Data2, Data3, Data4, Data5, CRC8]
[0xAA,    0x55,    cmd,     d0,    d1,    d2,    d3,    d4,    d5,    crc]
```

#### Command Types

```python
# Velocity command (0x64)
VELOCITY_CMD = 0x64

# Position command (0x65) 
POSITION_CMD = 0x65

# Current command (0x66)
CURRENT_CMD = 0x66

# Feedback request (0x74)
FEEDBACK_CMD = 0x74

# Motor ID set (0x53)
SET_ID_CMD = 0x53
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