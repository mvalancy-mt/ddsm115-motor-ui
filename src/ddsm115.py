#!/usr/bin/env python3
"""
DDSM115 Motor Control Core Library
Direct Drive Servo Motor control via RS485

This library provides low-level control of DDSM115 motors without any UI dependencies.
"""

import serial
import struct
import time
import threading
import signal
import atexit
import weakref
from typing import Optional, Dict, Tuple, List, Callable
from dataclasses import dataclass
from enum import IntEnum
from collections import deque


# Global registry for emergency shutdown
_active_motors = weakref.WeakSet()

def _emergency_shutdown():
    """Emergency shutdown handler for all active motors"""
    for motor in list(_active_motors):
        try:
            motor._emergency_stop_all()
        except:
            pass

# Register emergency shutdown
atexit.register(_emergency_shutdown)
signal.signal(signal.SIGTERM, lambda sig, frame: _emergency_shutdown())
signal.signal(signal.SIGINT, lambda sig, frame: _emergency_shutdown())


class MotorMode(IntEnum):
    """Motor control modes"""
    CURRENT = 0x01
    VELOCITY = 0x02
    POSITION = 0x03


class CommandType(IntEnum):
    """Command types for DDSM115 protocol"""
    EMERGENCY_STOP = 0x05
    MODE_SWITCH = 0xA0
    DRIVE_MOTOR = 0x64  # Used for velocity, current, and position control
    FEEDBACK_REQUEST = 0x74
    SET_ID = 0x53  # Corrected from 0x55
    QUERY_ID = 0xAA
    BRAKE = 0x90
    RELEASE_BRAKE = 0x91
    ENABLE = 0x88  # Motor enable command that was working in old GUI
    DISABLE = 0x93
    POSITION_CALIBRATION = 0x94


@dataclass
class MotorFeedback:
    """Motor feedback data structure"""
    position: float = 0.0  # degrees
    velocity: float = 0.0  # RPM
    torque: float = 0.0    # current in Amps
    temperature: int = 0   # Celsius
    raw_data: bytes = b''
    timestamp: float = 0.0


class DDSM115:
    """Core library for DDSM115 motor control"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, timeout: float = 0.2, 
                 suppress_comm_errors: bool = True):
        """
        Initialize DDSM115 motor controller
        
        Args:
            port: Serial port path
            baudrate: Communication baudrate (default 115200)
            timeout: Serial timeout in seconds
            suppress_comm_errors: If True, suppress non-critical communication errors
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.suppress_comm_errors = suppress_comm_errors
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        
        # Callbacks
        self.on_feedback: Optional[Callable[[int, MotorFeedback], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # State
        self.current_mode: Dict[int, MotorMode] = {}
        self.last_feedback: Dict[int, MotorFeedback] = {}
        
        # Memory management
        self._feedback_history_limit = 100  # Keep last 100 feedback entries per motor
        self._feedback_history: Dict[int, deque] = {}
        
        # Thread control
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._monitor_interval = 0.05  # 50ms default
        self._monitored_motors: List[int] = []
        
        # Register for emergency shutdown
        _active_motors.add(self)
    
    def connect(self) -> bool:
        """
        Connect to the motor controller
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            self.serial_port = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # Clear any pending data
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            
            self.is_connected = True
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Connection failed: {str(e)}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the motor controller"""
        self._emergency_stop_all()
    
    def _emergency_stop_all(self):
        """Emergency stop all motors and close connection safely"""
        try:
            # Stop monitoring first
            self.stop_monitoring()
            
            # Try multiple methods to stop motors
            if self.is_connected and self.serial_port:
                # Method 1: Stop all known motors
                for motor_id in list(self.current_mode.keys()):
                    try:
                        self._safe_emergency_stop(motor_id)
                    except:
                        pass
                
                # Method 2: Broadcast stop to common motor IDs
                for motor_id in range(1, 11):
                    try:
                        self._safe_emergency_stop(motor_id)
                    except:
                        pass
                
                # Allow time for commands to process
                time.sleep(0.1)
                
                # Close port
                if self.serial_port.is_open:
                    self.serial_port.close()
                    
        except Exception as e:
            # Suppress errors during emergency shutdown
            pass
        finally:
            self.is_connected = False
            self.serial_port = None
    
    def _safe_emergency_stop(self, motor_id: int):
        """Send emergency stop with minimal error handling"""
        try:
            # Send emergency stop
            packet = [motor_id, CommandType.EMERGENCY_STOP] + [0]*7
            crc = self.calculate_crc(packet)
            packet.append(crc)
            self.serial_port.write(bytes(packet))
            
            # Set to velocity mode with zero speed
            time.sleep(0.01)
            packet = [motor_id, CommandType.MODE_SWITCH, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02]
            crc = self.calculate_crc(packet)
            packet.append(crc)
            self.serial_port.write(bytes(packet))
            
            time.sleep(0.01)
            packet = [motor_id, CommandType.DRIVE_MOTOR, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            crc = self.calculate_crc(packet)
            packet.append(crc)
            self.serial_port.write(bytes(packet))
            
        except:
            pass
    
    def crc8_update(self, crc: int, data_byte: int) -> int:
        """
        CRC-8/MAXIM-DOW calculation (Dallas One-Wire)
        Polynomial: 0x8C (reverse of 0x31)
        """
        crc = crc ^ data_byte
        for _ in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
        return crc
    
    def calculate_crc(self, data: List[int]) -> int:
        """Calculate CRC for data packet"""
        crc = 0x00
        for byte in data:
            crc = self.crc8_update(crc, byte)
        return crc
    
    def send_packet(self, motor_id: int, command: int, data: List[int]) -> bool:
        """
        Send a command packet to the motor
        
        Args:
            motor_id: Motor ID (1-10)
            command: Command byte
            data: 7 bytes of data
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_connected or not self.serial_port:
            return False
        
        # Build packet: [ID, CMD, DATA[7], CRC]
        packet = [motor_id, command] + data[:7]
        
        # Pad with zeros if needed
        while len(packet) < 9:
            packet.append(0x00)
        
        # Calculate and append CRC
        crc = self.calculate_crc(packet)
        packet.append(crc)
        
        # Track last command for response parsing
        self._last_command = command
        
        try:
            self.serial_port.write(bytes(packet))
            return True
        except Exception as e:
            error_msg = str(e).lower()
            # Skip logging for common non-critical errors (more comprehensive)
            skip_patterns = [
                "device reports readiness to read but returned no data",
                "device disconnected",
                "multiple access on port",
                "returned no data",
                "device reports readiness",
                "access on port",
                "timeout",
                "resource busy"
            ]
            
            # Only log if it's not a known non-critical error and error logging is enabled
            if self.suppress_comm_errors:
                # Suppress all communication errors when flag is set
                if not any(pattern in error_msg for pattern in skip_patterns):
                    if self.on_error:
                        self.on_error(f"Send error: {str(e)}")
            else:
                # Log all errors when suppression is disabled
                if self.on_error:
                    self.on_error(f"Send error: {str(e)}")
            return False
    
    def read_response(self, expected_id: int = None, timeout: float = None) -> Optional[bytes]:
        """
        Read response from motor
        
        Args:
            expected_id: Expected motor ID (None for any)
            timeout: Custom timeout (uses default if None)
            
        Returns:
            bytes: Response data or None
        """
        if not self.is_connected or not self.serial_port:
            return None
        
        if timeout:
            old_timeout = self.serial_port.timeout
            self.serial_port.timeout = timeout
        
        try:
            response = self.serial_port.read(10)
            
            if len(response) == 10:
                # Verify CRC
                crc_calc = self.calculate_crc(list(response[:9]))
                if crc_calc == response[9]:
                    # Check motor ID if specified
                    if expected_id is None or response[0] == expected_id:
                        return response
                    
            return None
            
        except Exception as e:
            error_msg = str(e).lower()
            # Skip logging for common non-critical errors (more comprehensive)
            skip_patterns = [
                "device reports readiness to read but returned no data",
                "device disconnected", 
                "multiple access on port",
                "returned no data",
                "device reports readiness",
                "access on port",
                "timeout",
                "resource busy"
            ]
            
            # Only log if it's not a known non-critical error and error logging is enabled
            if self.suppress_comm_errors:
                # Suppress all communication errors when flag is set
                if not any(pattern in error_msg for pattern in skip_patterns):
                    if self.on_error:
                        self.on_error(f"Read error: {str(e)}")
            else:
                # Log all errors when suppression is disabled
                if self.on_error:
                    self.on_error(f"Read error: {str(e)}")
            return None
        finally:
            if timeout:
                self.serial_port.timeout = old_timeout
    
    def set_mode(self, motor_id: int, mode: MotorMode) -> bool:
        """
        Set motor control mode
        
        Args:
            motor_id: Motor ID
            mode: Control mode (CURRENT, VELOCITY, POSITION)
            
        Returns:
            bool: True if successful
        """
        # Format: ID A0 00 00 00 00 00 00 00 MODE_VALUE CRC
        # Mode value must be in the 10th byte position according to protocol examples
        
        if not self.is_connected or not self.serial_port:
            return False
        
        # Use 10-byte format (no CRC) as per reference implementation
        # Format: ID A0 00 00 00 00 00 00 00 MODE_VALUE
        import struct
        packet_data = struct.pack(">BBBBBBBBBB", motor_id, CommandType.MODE_SWITCH, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, int(mode))
        
        try:
            self.serial_port.write(packet_data)
            self.current_mode[motor_id] = mode
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"Mode switch error: {str(e)}")
            return False
    
    def set_velocity(self, motor_id: int, rpm: float) -> bool:
        """
        Set motor velocity (-143 to 143 RPM)
        
        Args:
            motor_id: Motor ID
            rpm: Target velocity in RPM
            
        Returns:
            bool: True if successful
        """
        # Ensure velocity mode
        if motor_id not in self.current_mode or self.current_mode[motor_id] != MotorMode.VELOCITY:
            if not self.set_mode(motor_id, MotorMode.VELOCITY):
                return False
            time.sleep(0.01)
        
        # Clamp RPM
        rpm = max(-143, min(143, rpm))
        rpm_int = int(rpm)
        
        # Pack as signed 16-bit in bytes 2-3
        data = list(struct.pack('>h', rpm_int))
        data.extend([0x00, 0x00, 0x00, 0x00, 0x00])
        
        return self.send_packet(motor_id, CommandType.DRIVE_MOTOR, data)
    
    def set_current(self, motor_id: int, current: float, auto_switch_mode: bool = True) -> bool:
        """
        Set motor current (-8A to 8A)
        
        Args:
            motor_id: Motor ID
            current: Target current in Amps
            auto_switch_mode: Whether to automatically switch to current mode
            
        Returns:
            bool: True if successful
        """
        # Ensure current mode (only if auto_switch_mode is True)
        if auto_switch_mode:
            if motor_id not in self.current_mode or self.current_mode[motor_id] != MotorMode.CURRENT:
                if not self.set_mode(motor_id, MotorMode.CURRENT):
                    return False
                time.sleep(0.01)
        
        # Clamp current and convert to 0.01A units
        current = max(-8, min(8, current))
        current_int = int(current * 100)  # Convert to 0.01A units
        
        # Pack as signed 16-bit in bytes 2-3
        data = list(struct.pack('>h', current_int))
        data.extend([0x00, 0x00, 0x00, 0x00, 0x00])
        
        return self.send_packet(motor_id, CommandType.DRIVE_MOTOR, data)
    
    def set_position(self, motor_id: int, degrees: float) -> bool:
        """
        Set motor position (0-360 degrees)
        
        Args:
            motor_id: Motor ID
            degrees: Target position in degrees
            
        Returns:
            bool: True if successful
        """
        # Ensure position mode
        if motor_id not in self.current_mode or self.current_mode[motor_id] != MotorMode.POSITION:
            if not self.set_mode(motor_id, MotorMode.POSITION):
                return False
            time.sleep(0.01)
        
        # Clamp and scale (0-32767 for 0-360 degrees)
        degrees = max(0, min(360, degrees))
        position = int((degrees / 360.0) * 32767)
        
        # Pack as unsigned 16-bit in bytes 2-3
        data = list(struct.pack('>H', position))
        data.extend([0x00, 0x00, 0x00, 0x00, 0x00])
        
        return self.send_packet(motor_id, CommandType.DRIVE_MOTOR, data)
    
    def emergency_stop(self, motor_id: int) -> bool:
        """Send emergency stop command"""
        success = self.send_packet(motor_id, CommandType.EMERGENCY_STOP, [0]*7)
        
        # Switch to velocity mode with zero speed
        if success:
            time.sleep(0.01)
            self.set_mode(motor_id, MotorMode.VELOCITY)
            time.sleep(0.01)
            self.set_velocity(motor_id, 0)
            
        return success
    
    def brake(self, motor_id: int) -> bool:
        """Apply motor brake"""
        return self.send_packet(motor_id, CommandType.BRAKE, [0]*7)
    
    def release_brake(self, motor_id: int) -> bool:
        """Release motor brake"""
        return self.send_packet(motor_id, CommandType.RELEASE_BRAKE, [0]*7)
    
    def enable(self, motor_id: int) -> bool:
        """Enable motor"""
        return self.send_packet(motor_id, CommandType.ENABLE, [0]*7)
    
    def disable(self, motor_id: int) -> bool:
        """Disable motor"""
        return self.send_packet(motor_id, CommandType.DISABLE, [0]*7)
    
    def calibrate_position(self, motor_id: int) -> bool:
        """Calibrate motor position"""
        return self.send_packet(motor_id, CommandType.POSITION_CALIBRATION, [0]*7)
    
    def request_feedback(self, motor_id: int) -> Optional[MotorFeedback]:
        """
        Request feedback from motor
        
        Args:
            motor_id: Motor ID
            
        Returns:
            MotorFeedback or None
        """
        if self.send_packet(motor_id, CommandType.FEEDBACK_REQUEST, [0]*7):
            response = self.read_response(motor_id, timeout=0.1)
            
            if response and len(response) == 10:
                feedback = self.parse_feedback(response)
                self.last_feedback[motor_id] = feedback
                
                # Store in bounded history for memory management
                if motor_id not in self._feedback_history:
                    self._feedback_history[motor_id] = deque(maxlen=self._feedback_history_limit)
                self._feedback_history[motor_id].append(feedback)
                
                if self.on_feedback:
                    self.on_feedback(motor_id, feedback)
                    
                return feedback
                
        return None
    
    def parse_feedback(self, data: bytes) -> MotorFeedback:
        """Parse feedback data from motor response
        
        Two different response formats:
        1. Standard response (non-0x74):
           DATA[0]: Motor ID
           DATA[1]: Mode value (0x01=Current, 0x02=Velocity, 0x03=Position)
           DATA[2-3]: Torque current (high/low bytes, signed)
           DATA[4-5]: Velocity (high/low bytes, signed)
           DATA[6-7]: Position (high/low bytes, unsigned, 0-32767 = 0-360°)
           DATA[8]: Error code
           DATA[9]: CRC8
        
        2. 0x74 feedback response:
           DATA[0]: Motor ID
           DATA[1]: Mode value
           DATA[2-3]: Torque current (high/low bytes)
           DATA[4-5]: Velocity (high/low bytes)
           DATA[6]: Winding temperature (°C)
           DATA[7]: U8 position value (0-255 = 0-360°)
           DATA[8]: Error code
           DATA[9]: CRC8
        """
        feedback = MotorFeedback()
        feedback.raw_data = data
        feedback.timestamp = time.time()
        
        if len(data) >= 10:
            mode = data[1]
            
            # Torque/Current: bytes 2-3 (signed, in 0.01A units)
            torque_raw = struct.unpack('>h', data[2:4])[0]
            feedback.torque = torque_raw / 100.0  # Convert to Amps
            
            # Velocity: bytes 4-5 (signed, direct RPM)
            velocity_raw = struct.unpack('>h', data[4:6])[0]
            feedback.velocity = velocity_raw
            
            # Check if this is a 0x74 response by looking at the command we sent
            # In 0x74 response format:
            if hasattr(self, '_last_command') and self._last_command == CommandType.FEEDBACK_REQUEST:
                # Temperature: byte 6 (direct °C value)
                feedback.temperature = data[6]
                # Position: byte 7 (0-255 = 0-360°)
                position_raw = data[7]
                feedback.position = (position_raw / 255.0) * 360.0
            else:
                # Standard response format
                # Position: bytes 6-7 (unsigned, 0-32767 = 0-360°)
                position_raw = struct.unpack('>H', data[6:8])[0]
                feedback.position = (position_raw / 32767.0) * 360.0
                feedback.temperature = 0
            
        return feedback
    
    def scan_motors(self, start_id: int = 1, end_id: int = 10) -> List[int]:
        """
        Scan for motors on the bus
        
        Args:
            start_id: Starting motor ID
            end_id: Ending motor ID
            
        Returns:
            List of found motor IDs
        """
        found_motors = []
        
        for motor_id in range(start_id, end_id + 1):
            # Try to get feedback
            if self.request_feedback(motor_id):
                found_motors.append(motor_id)
                time.sleep(0.01)
                
        return found_motors
    
    def set_motor_id(self, old_id: int, new_id: int) -> bool:
        """
        Change motor ID (requires sending command 5 times)
        Protocol: [0xAA, 0x55, 0x53, new_id, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        Args:
            old_id: Current motor ID (not used in protocol, but kept for compatibility)  
            new_id: New motor ID
            
        Returns:
            bool: True if successful
        """
        if new_id < 1 or new_id > 10:
            return False
        
        # Raw protocol format for SET_ID
        raw_packet = [0xAA, 0x55, 0x53, new_id, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        # Send SET_ID command 5 times as required
        for i in range(5):
            try:
                if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                    self.serial_port.write(bytes(raw_packet))
                    self.serial_port.flush()
                else:
                    return False
            except Exception as e:
                print(f"Error sending SET_ID packet {i+1}: {e}")
                return False
            time.sleep(0.05)
        
        # Wait for motor to process the ID change  
        time.sleep(0.1)
        
        # Verify by requesting feedback with new ID
        return self.request_feedback(new_id) is not None
    
    def start_monitoring(self, motor_ids: List[int], interval: float = 0.05):
        """
        Start automatic motor monitoring
        
        Args:
            motor_ids: List of motor IDs to monitor
            interval: Update interval in seconds
        """
        self.stop_monitoring()
        
        self._monitored_motors = motor_ids
        self._monitor_interval = interval
        self._monitoring_active = True
        
        self._monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop automatic motor monitoring"""
        self._monitoring_active = False
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=1.0)
            self._monitoring_thread = None
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active and self.is_connected:
            for motor_id in self._monitored_motors:
                if not self._monitoring_active:
                    break
                    
                self.request_feedback(motor_id)
                time.sleep(0.01)  # Small delay between motors
                
            # Wait for next cycle
            remaining = self._monitor_interval - (0.01 * len(self._monitored_motors))
            if remaining > 0:
                time.sleep(remaining)
    
    def get_last_feedback(self, motor_id: int) -> Optional[MotorFeedback]:
        """Get last received feedback for a motor"""
        return self.last_feedback.get(motor_id)
    
    def get_feedback_history(self, motor_id: int) -> List[MotorFeedback]:
        """Get feedback history for a motor (bounded list)"""
        if motor_id in self._feedback_history:
            return list(self._feedback_history[motor_id])
        return []
    
    def clear_feedback_history(self, motor_id: int = None):
        """Clear feedback history for specific motor or all motors"""
        if motor_id is None:
            self._feedback_history.clear()
        elif motor_id in self._feedback_history:
            self._feedback_history[motor_id].clear()
    
    def is_motor_connected(self, motor_id: int) -> bool:
        """Check if a specific motor is responding"""
        return self.request_feedback(motor_id) is not None
    
    def __enter__(self):
        """Context manager entry"""
        if not self.connect():
            raise RuntimeError(f"Failed to connect to motor controller on {self.port}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures motors are stopped"""
        self._emergency_stop_all()
    
    def __del__(self):
        """Destructor - emergency stop as last resort"""
        try:
            self._emergency_stop_all()
        except:
            pass


def example_usage():
    """Example of using the DDSM115 library with safe shutdown"""
    # Set up callbacks
    def on_feedback(motor_id: int, feedback: MotorFeedback):
        print(f"Motor {motor_id}: Pos={feedback.position:.1f}° "
              f"Vel={feedback.velocity:.1f}RPM "
              f"Torque={feedback.torque:.2f}A "
              f"Temp={feedback.temperature}°C")
    
    def on_error(error: str):
        print(f"Error: {error}")
    
    # Use context manager for automatic cleanup
    try:
        with DDSM115(port="/dev/ttyUSB0") as motor:
            motor.on_feedback = on_feedback
            motor.on_error = on_error
            
            print("Connected!")
            
            # Scan for motors
            found = motor.scan_motors()
            print(f"Found motors: {found}")
            
            if found:
                motor_id = found[0]
                
                # Start monitoring
                motor.start_monitoring([motor_id], interval=0.1)
                
                # Velocity control
                print("Setting velocity to 50 RPM...")
                motor.set_velocity(motor_id, 50)
                time.sleep(3)
                
                # Stop
                print("Stopping...")
                motor.set_velocity(motor_id, 0)
                time.sleep(1)
                
                # Position control
                print("Moving to 180 degrees...")
                motor.set_position(motor_id, 180)
                time.sleep(3)
                
        print("Motors safely stopped and disconnected")
        
    except KeyboardInterrupt:
        print("Interrupted - motors stopped safely")
    except Exception as e:
        print(f"Error: {e} - motors stopped safely")


if __name__ == "__main__":
    example_usage()