#!/usr/bin/env python3
"""
DDSM210 Motor Control Core Library
Direct Drive Servo Motor control via USB-Serial

This library provides DDSM210 motor control following the same interface as DDSM115
but with the proven protocol implementation reverse-engineered from the hardware.
"""

import serial
import time
import threading
import signal
import atexit
import weakref
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from enum import IntEnum
from collections import deque


# Import base classes from DDSM115 for compatibility
try:
    from .ddsm115 import MotorFeedback, _active_motors
except ImportError:
    from ddsm115 import MotorFeedback, _active_motors


class DDSM210Mode(IntEnum):
    """Motor control modes for DDSM210"""
    VELOCITY = 0x02  # Only velocity mode is supported in hardware
    # Position mode (0x03) documented but not working in this motor variant


class DDSM210CommandType(IntEnum):
    """Command types for DDSM210 protocol (reverse-engineered)"""
    MODE_SWITCH = 0xA0      # Switch between control modes
    DRIVE_MOTOR = 0x64      # Velocity control command  
    MODE_QUERY = 0x75       # Query current motor mode
    ID_QUERY = 0xC8         # Query motor ID (broadcast)
    ID_SETTING = 0xAA       # Set motor ID (requires specific sequence)
    EMERGENCY_BRAKE = 0xFF  # Emergency brake (special data[7] value)


class DDSM210:
    """Core library for DDSM210 motor control - compatible with DDSM115 interface"""
    
    def __init__(self, port: str = "/dev/ttyACM1", baudrate: int = 115200, timeout: float = 1.0, 
                 suppress_comm_errors: bool = True):
        """
        Initialize DDSM210 motor controller
        
        Args:
            port: Serial port path (typically /dev/ttyACM1 for DDSM210)
            baudrate: Communication baudrate (115200 for DDSM210)
            timeout: Serial timeout in seconds
            suppress_comm_errors: If True, suppress non-critical communication errors
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.suppress_comm_errors = suppress_comm_errors
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.motor_id = 0x01  # DDSM210 uses fixed ID 0x01
        
        # Callbacks - same interface as DDSM115
        self.on_feedback: Optional[Callable[[int, MotorFeedback], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_tx: Optional[Callable[[], None]] = None
        
        # State
        self.current_mode: Dict[int, DDSM210Mode] = {}
        self.last_feedback: Dict[int, MotorFeedback] = {}
        
        # Memory management
        self._feedback_history_limit = 100
        self._feedback_history: Dict[int, deque] = {}
        
        # Thread control
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._monitor_interval = 0.1  # 100ms default (slower than DDSM115)
        self._monitored_motors: List[int] = []
        
        # DDSM210 specific state
        self._motor_initialized = False
        self._current_velocity = 0.0  # Track current commanded velocity
        
        # Register for emergency shutdown
        _active_motors.add(self)
    
    def connect(self) -> bool:
        """
        Connect to the DDSM210 motor controller
        
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
            
            # Try to initialize motor immediately
            if self._initialize_motor():
                self._motor_initialized = True
            
            return True
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"DDSM210 connection failed: {str(e)}")
            self.is_connected = False
            return False
    
    def _initialize_motor(self) -> bool:
        """Initialize DDSM210 motor with required sequence"""
        try:
            # Send ID setting command 5 times (required for DDSM210)
            id_cmd = [0xAA, 0x55, 0x53, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0xCB]
            for i in range(5):
                self._send_raw_command(id_cmd)
                time.sleep(0.1)
            
            # Switch to velocity mode
            return self._set_velocity_mode()
            
        except Exception as e:
            if not self.suppress_comm_errors and self.on_error:
                self.on_error(f"DDSM210 initialization failed: {str(e)}")
            return False
    
    def _set_velocity_mode(self) -> bool:
        """Switch DDSM210 to velocity mode"""
        try:
            cmd = [0x01, 0xA0, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            crc = self._calculate_crc(cmd)
            cmd.append(crc)
            
            self._send_raw_command(cmd)
            time.sleep(0.5)
            
            # Update state
            self.current_mode[self.motor_id] = DDSM210Mode.VELOCITY
            return True
            
        except Exception as e:
            if not self.suppress_comm_errors and self.on_error:
                self.on_error(f"Velocity mode switch failed: {str(e)}")
            return False
    
    def _calculate_crc(self, data: List[int]) -> int:
        """
        Calculate Reflected CRC-8/MAXIM for DDSM210
        This is the proven algorithm from our reverse-engineering work
        """
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x01:  # Check LSB for reflected algorithm
                    crc = (crc >> 1) ^ 0x8C  # Reflected polynomial
                else:
                    crc >>= 1
        return crc
    
    def _send_raw_command(self, command: List[int]) -> Optional[bytes]:
        """Send raw command to motor and read response"""
        if not self.is_connected or not self.serial_port:
            return None
        
        try:
            # Send command
            self.serial_port.write(bytes(command))
            self.serial_port.flush()
            
            # Increment TX counter if callback is available
            if self.on_tx:
                self.on_tx()
            
            # Read response (DDSM210 always sends 10-byte responses when available)
            response = self.serial_port.read(10)
            return response if len(response) == 10 else None
            
        except Exception as e:
            if not self.suppress_comm_errors and self.on_error:
                self.on_error(f"Communication error: {str(e)}")
            return None
    
    def scan_motors(self, start_id: int = 1, end_id: int = 10) -> List[int]:
        """
        Scan for DDSM210 motors (always returns [1] since DDSM210 uses fixed ID)
        Parameters are ignored for compatibility with DDSM115 interface
        
        Args:
            start_id: Ignored (for DDSM115 compatibility)
            end_id: Ignored (for DDSM115 compatibility)
            
        Returns:
            List[int]: List of detected motor IDs
        """
        if not self.is_connected:
            return []
        
        try:
            # Query motor ID
            id_cmd = [0xC8, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xDE]
            response = self._send_raw_command(id_cmd)
            
            if response and len(response) >= 1:
                # DDSM210 responds, so motor ID 1 is present
                return [1]
            else:
                return []
                
        except Exception as e:
            if not self.suppress_comm_errors and self.on_error:
                self.on_error(f"Motor scan failed: {str(e)}")
            return []
    
    def set_velocity(self, motor_id: int, rpm: float) -> bool:
        """
        Set motor velocity (DDSM115-compatible interface)
        
        Args:
            motor_id: Motor ID (ignored for DDSM210, always uses ID 1)
            rpm: Velocity in RPM (-210 to 210)
            
        Returns:
            bool: True if command sent successfully
        """
        if not self.is_connected or not self._motor_initialized:
            return False
        
        # Clamp to DDSM210 range
        rpm = max(-210, min(210, rpm))
        
        # Track the current velocity
        self._current_velocity = rpm
        
        try:
            # Ensure motor is in velocity mode
            if self.motor_id not in self.current_mode:
                self._initialize_motor()
            
            # Convert RPM to velocity units (0.1 RPM resolution)
            velocity_units = int(rpm * 10)
            if velocity_units < 0:
                velocity_units = velocity_units & 0xFFFF  # Two's complement
            
            # DDSM210 uses big-endian format for velocity
            high_byte = (velocity_units >> 8) & 0xFF
            low_byte = velocity_units & 0xFF
            
            # Build command
            cmd = [0x01, 0x64, high_byte, low_byte, 0x00, 0x00, 0x00, 0x00, 0x00]
            crc = self._calculate_crc(cmd)
            cmd.append(crc)
            
            # Send command
            response = self._send_raw_command(cmd)
            
            # Update feedback with commanded velocity (DDSM210 doesn't return actual feedback)
            if response:
                feedback = MotorFeedback()
                feedback.raw_data = response
                feedback.timestamp = time.time()
                feedback.velocity = rpm  # Use commanded velocity as feedback
                feedback.position = 0.0  # DDSM210 doesn't provide position
                feedback.torque = 0.0    # DDSM210 doesn't provide torque
                feedback.temperature = 0.0  # DDSM210 doesn't provide temperature
                
                # DDSM210 doesn't provide position feedback - always show 0
                feedback.position = 0.0
                
                self.last_feedback[self.motor_id] = feedback
                
                if self.on_feedback:
                    self.on_feedback(self.motor_id, feedback)
            
            return True
            
        except Exception as e:
            if not self.suppress_comm_errors and self.on_error:
                self.on_error(f"Set velocity failed: {str(e)}")
            return False
    
    def set_mode(self, motor_id: int, mode) -> bool:
        """
        Set motor mode (DDSM115-compatible interface)
        DDSM210 only supports velocity mode, so this always sets velocity mode
        
        Args:
            motor_id: Motor ID (ignored for DDSM210)
            mode: Motor mode (ignored - DDSM210 only supports velocity)
            
        Returns:
            bool: True if mode set successfully
        """
        if not self.is_connected:
            return False
        
        # DDSM210 only supports velocity mode
        return self._set_velocity_mode()
    
    def emergency_stop(self, motor_id: int) -> bool:
        """
        Emergency stop for specified motor (DDSM115-compatible interface)
        
        Args:
            motor_id: Motor ID (ignored for DDSM210)
            
        Returns:
            bool: True if command sent successfully
        """
        if not self.is_connected:
            return False
        
        try:
            # DDSM210 brake command (exact working command)
            brake_cmd = [0x01, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xD1]
            response = self._send_raw_command(brake_cmd)
            
            # Reset current velocity on emergency stop
            self._current_velocity = 0.0
            
            return response is not None
            
        except Exception as e:
            if not self.suppress_comm_errors and self.on_error:
                self.on_error(f"Emergency stop failed: {str(e)}")
            return False
    
    def request_feedback(self, motor_id: int) -> Optional[MotorFeedback]:
        """
        Request feedback from motor (DDSM115-compatible interface)
        For DDSM210, this returns the current commanded velocity as feedback
        
        Args:
            motor_id: Motor ID (ignored for DDSM210)
            
        Returns:
            MotorFeedback: Motor feedback data or None if failed
        """
        if not self.is_connected:
            return None
        
        try:
            # When motor is idle (velocity = 0), send a ping to verify it's alive
            if self._current_velocity == 0.0:
                # Send mode query command as a "ping" to check if motor is responsive
                mode_cmd = [0x01, 0x75, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x47]
                
                # Debug: log ping attempt
                if self.on_error:
                    self.on_error(f"🏓 DDSM210 sending ping command (velocity={self._current_velocity})")
                
                response = self._send_raw_command(mode_cmd)
                
                if response and len(response) >= 3:
                    # Motor responded - it's alive!
                    if response[1] == 0x75 and response[2] == 0x02:
                        # Confirmed in velocity mode and responding
                        if not self.suppress_comm_errors and self.on_error:
                            hex_resp = ' '.join(f'{b:02X}' for b in response[:4])
                            self.on_error(f"✅ DDSM210 ping OK: {hex_resp}")
                    else:
                        if not self.suppress_comm_errors and self.on_error:
                            hex_resp = ' '.join(f'{b:02X}' for b in response)
                            self.on_error(f"⚠️ DDSM210 ping unexpected response: {hex_resp}")
                else:
                    # No response - motor might be disconnected
                    if not self.suppress_comm_errors and self.on_error:
                        self.on_error("❌ DDSM210 ping failed - no response")
            
            # Return current motor state feedback
            feedback = MotorFeedback()
            feedback.timestamp = time.time()
            feedback.velocity = self._current_velocity  # Use commanded velocity
            feedback.position = 0.0  # DDSM210 doesn't provide position
            feedback.torque = 0.0    # DDSM210 doesn't provide torque
            feedback.temperature = 0.0  # DDSM210 doesn't provide temperature
            
            self.last_feedback[self.motor_id] = feedback
            return feedback
                
        except Exception as e:
            if not self.suppress_comm_errors and self.on_error:
                self.on_error(f"Feedback request failed: {str(e)}")
            return None
    
    def _parse_feedback(self, response: bytes) -> MotorFeedback:
        """Parse DDSM210 response into MotorFeedback structure"""
        feedback = MotorFeedback()
        feedback.raw_data = response
        feedback.timestamp = time.time()
        
        # Initialize with default values
        feedback.velocity = 0.0
        feedback.position = 0.0
        feedback.torque = 0.0
        feedback.temperature = 0.0
        
        if len(response) >= 10:
            try:
                # DDSM210 response format analysis from our working commands
                if response[1] == 0x64:  # Velocity command response
                    # For DDSM210, the response typically echoes back the command
                    # The actual velocity might be in the response, let's parse it
                    velocity_raw = (response[2] << 8) | response[3]
                    if velocity_raw > 32767:  # Handle negative values (two's complement)
                        velocity_raw -= 65536
                    feedback.velocity = velocity_raw / 10.0  # Convert to RPM (0.1 RPM resolution)
                    
                    # DDSM210 response parsing (currently not used - we track commanded velocity instead)
                    
                elif response[1] == 0x75:  # Mode query response
                    mode_val = response[2]
                    if mode_val == 0x02:
                        # In velocity mode, try to get current status
                        feedback.velocity = 0.0  # Default when just querying mode
                        
                elif response[1] == 0xA0:  # Mode confirmation response
                    mode_val = response[2]
                    feedback.velocity = 0.0  # Mode switch confirmation
                
            except Exception as e:
                if not self.suppress_comm_errors and self.on_error:
                    self.on_error(f"Feedback parsing error: {str(e)}")
        
        return feedback
    
    def start_monitoring(self, motor_ids: List[int], interval: float = 0.1):
        """
        Start monitoring motors (DDSM115-compatible interface)
        
        Args:
            motor_ids: List of motor IDs to monitor (DDSM210 always monitors ID 1)
            interval: Monitoring interval in seconds
        """
        if self._monitoring_active:
            self.stop_monitoring()
        
        self._monitor_interval = max(0.1, interval)  # Minimum 100ms for DDSM210
        self._monitored_motors = [1]  # DDSM210 always uses ID 1
        self._monitoring_active = True
        
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring motors"""
        self._monitoring_active = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=1.0)
    
    def _monitoring_loop(self):
        """Background monitoring loop with adaptive interval"""
        while self._monitoring_active:
            try:
                for motor_id in self._monitored_motors:
                    if not self._monitoring_active:
                        break
                    
                    feedback = self.request_feedback(motor_id)
                    if feedback and self.on_feedback:
                        self.on_feedback(motor_id, feedback)
                
                # Adaptive monitoring interval:
                # - 1.0s when motor is idle (acts as connection ping)
                # - 0.1s when motor is running (for real-time feedback)
                if self._current_velocity == 0.0:
                    sleep_time = 1.0  # 1 second ping when idle
                    # Debug: log monitoring when idle
                    if self.on_error:
                        self.on_error(f"⏱️ DDSM210 monitoring loop - idle mode, sleeping {sleep_time}s")
                else:
                    sleep_time = self._monitor_interval  # Fast updates when running
                    
                time.sleep(sleep_time)
                
            except Exception as e:
                if not self.suppress_comm_errors and self.on_error:
                    self.on_error(f"Monitoring error: {str(e)}")
                time.sleep(self._monitor_interval)
    
    def _emergency_stop_all(self):
        """Emergency stop all motors"""
        if self.is_connected:
            self.emergency_stop(1)
    
    def disconnect(self):
        """Disconnect from the motor controller"""
        self._emergency_stop_all()
        self.stop_monitoring()
        
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
        
        self.is_connected = False
        self._motor_initialized = False
    
    def __del__(self):
        """Cleanup on destruction"""
        self.disconnect()


# For compatibility, provide the same interface functions as DDSM115
def scan_ports() -> List[str]:
    """Scan for available serial ports that might have DDSM210 motors"""
    import glob
    import platform
    
    if platform.system() == "Windows":
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif platform.system() == "Darwin":
        ports = glob.glob('/dev/tty.*')
    else:
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    
    available_ports = []
    for port in ports:
        try:
            s = serial.Serial(port, timeout=0.1)
            s.close()
            available_ports.append(port)
        except (OSError, serial.SerialException):
            pass
    
    return available_ports