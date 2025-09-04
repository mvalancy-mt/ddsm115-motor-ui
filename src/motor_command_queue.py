#!/usr/bin/env python3
"""
Motor Command Queue - Single point of contact for all motor commands
Prevents race conditions and command conflicts
"""

import time
import threading
import queue
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum
from ddsm115 import DDSM115, MotorMode, MotorFeedback
from ddsm210 import DDSM210

class CommandType(Enum):
    SET_VELOCITY = "set_velocity"
    SET_CURRENT = "set_current" 
    SET_POSITION = "set_position"
    SET_MODE = "set_mode"
    REQUEST_FEEDBACK = "request_feedback"
    ENABLE = "enable"
    DISABLE = "disable"
    STOP = "stop"

@dataclass
class MotorCommand:
    command_type: CommandType
    motor_id: int
    value: Any = None
    callback: Optional[Callable] = None
    priority: int = 1  # 1=normal, 2=high, 3=emergency
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class MotorCommandQueue:
    def __init__(self, port: str = "/dev/ttyUSB0", motor_type: str = "auto"):
        # Motor type can be "ddsm115", "ddsm210", or "auto" for detection
        self.motor_type = motor_type
        self.motor = None
        self.port = port
        
        # Initialize motor based on type
        if motor_type == "ddsm115":
            self.motor = DDSM115(port=port, suppress_comm_errors=False)
        elif motor_type == "ddsm210":
            self.motor = DDSM210(port=port, suppress_comm_errors=False)
        elif motor_type == "auto":
            # Will be detected during connection
            pass
        else:
            raise ValueError(f"Unknown motor type: {motor_type}")
        self.command_queue = queue.PriorityQueue()
        self.feedback_queue = queue.Queue()
        
        # Threading
        self.worker_thread: Optional[threading.Thread] = None
        self.feedback_thread: Optional[threading.Thread] = None
        self.running = False
        
        # State tracking
        self.current_mode: Dict[int, MotorMode] = {}
        self.last_feedback: Dict[int, MotorFeedback] = {}
        self.pending_mode_switches: Dict[int, MotorMode] = {}
        
        # Latest command tracking (keep only the most recent command of each type)
        self.latest_commands: Dict[tuple, MotorCommand] = {}  # Key: (motor_id, command_type)
        self.command_lock = threading.Lock()
        
        # Stats
        self.commands_processed = 0
        self.commands_failed = 0
        self.feedback_count = 0
        self.commands_dropped = 0  # Track dropped/replaced commands
        
        # Callbacks
        self.on_feedback: Optional[Callable[[int, MotorFeedback], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_command_sent: Optional[Callable[[], None]] = None  # Called when command is sent
        
        # Rate limiting
        self.last_command_time = 0
        self.min_command_interval = 0.005  # 5ms minimum between commands (faster processing)
        self.last_feedback_time = 0
        self.min_feedback_interval = 0.01  # 10ms minimum between feedback requests
    
    @property
    def is_connected(self) -> bool:
        """Check if motor is connected"""
        return self.motor.is_connected if self.motor else False
        
    def connect(self) -> bool:
        """Connect to motor and start processing"""
        # Auto-detect motor type if needed
        if self.motor_type == "auto":
            if not self._detect_motor_type():
                return False
        
        if not self.motor or not self.motor.connect():
            return False
        
        self.running = True
        
        # Start worker threads
        self.worker_thread = threading.Thread(target=self._command_worker, daemon=True)
        self.feedback_thread = threading.Thread(target=self._feedback_worker, daemon=True)
        
        self.worker_thread.start()
        self.feedback_thread.start()
        
        return True
    
    def _detect_motor_type(self) -> bool:
        """Auto-detect motor type by trying both DDSM115 and DDSM210"""
        # Try DDSM210 first (it uses ACM ports typically)
        if "/dev/ttyACM" in self.port:
            try:
                test_motor = DDSM210(port=self.port, suppress_comm_errors=True)
                if test_motor.connect():
                    test_motor.disconnect()
                    self.motor = DDSM210(port=self.port, suppress_comm_errors=False)
                    self.motor_type = "ddsm210"
                    return True
            except Exception:
                pass
        
        # Try DDSM115
        try:
            test_motor = DDSM115(port=self.port, suppress_comm_errors=True)
            if test_motor.connect():
                test_motor.disconnect()
                self.motor = DDSM115(port=self.port, suppress_comm_errors=False)
                self.motor_type = "ddsm115"
                return True
        except Exception:
            pass
        
        # Try DDSM210 on USB ports as fallback
        try:
            test_motor = DDSM210(port=self.port, suppress_comm_errors=True)
            if test_motor.connect():
                test_motor.disconnect()
                self.motor = DDSM210(port=self.port, suppress_comm_errors=False)
                self.motor_type = "ddsm210"
                return True
        except Exception:
            pass
            
        return False
    
    def get_motor_type(self) -> str:
        """Get the detected motor type"""
        return self.motor_type
    
    def disconnect(self):
        """Disconnect and stop processing"""
        self.running = False
        
        # Stop motor first
        if hasattr(self, 'motor') and self.motor.is_connected:
            for motor_id in self.current_mode.keys():
                try:
                    self.motor.set_velocity(motor_id, 0)
                except:
                    pass
        
        # Wait for threads to finish
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1)
        if self.feedback_thread and self.feedback_thread.is_alive():
            self.feedback_thread.join(timeout=1)
        
        self.motor.disconnect()
    
    def scan_motors(self, start_id: int = 1, end_id: int = 10) -> list:
        """Scan for motors and register them for feedback monitoring"""
        found_motors = self.motor.scan_motors(start_id, end_id)
        
        # Register found motors for feedback monitoring
        for motor_id in found_motors:
            if motor_id not in self.current_mode:
                # Initialize with unknown mode - will be updated by first feedback
                self.current_mode[motor_id] = None
        
        return found_motors
    
    # Public command interface
    def set_velocity(self, motor_id: int, velocity: float, callback: Optional[Callable] = None):
        """Queue velocity command"""
        cmd = MotorCommand(CommandType.SET_VELOCITY, motor_id, velocity, callback)
        self._queue_command(cmd)
    
    def set_current(self, motor_id: int, current: float, callback: Optional[Callable] = None):
        """Queue current command"""
        cmd = MotorCommand(CommandType.SET_CURRENT, motor_id, current, callback)
        self._queue_command(cmd)
    
    def set_position(self, motor_id: int, position: float, callback: Optional[Callable] = None):
        """Queue position command"""
        cmd = MotorCommand(CommandType.SET_POSITION, motor_id, position, callback)
        self._queue_command(cmd)
    
    def set_mode(self, motor_id: int, mode: MotorMode, callback: Optional[Callable] = None):
        """Queue mode switch command"""
        cmd = MotorCommand(CommandType.SET_MODE, motor_id, mode, callback, priority=2)  # Higher priority
        self._queue_command(cmd)
    
    def request_feedback(self, motor_id: int, callback: Optional[Callable] = None):
        """Request feedback immediately - bypasses queue for continuous monitoring"""
        # Rate limiting to prevent serial conflicts
        try:
            now = time.time()
            if now - self.last_feedback_time < self.min_feedback_interval:
                return None
        except Exception:
            # Time error, proceed anyway
            pass
        
        try:
            if not self.motor or not hasattr(self.motor, 'request_feedback'):
                return None
                
            feedback = self.motor.request_feedback(motor_id)
            
            try:
                self.last_feedback_time = time.time()
            except Exception:
                pass  # Ignore time update errors
            
            if feedback:
                try:
                    self.last_feedback[motor_id] = feedback
                    self.feedback_count += 1
                except Exception as e:
                    if self.on_error:
                        self.on_error(f"Feedback storage error: {e}")
                
                # Update current mode from feedback with validation
                try:
                    if hasattr(feedback, 'raw_data') and feedback.raw_data and len(feedback.raw_data) > 1:
                        mode_val = feedback.raw_data[1]
                        if isinstance(mode_val, int) and mode_val in [1, 2, 3]:
                            self.current_mode[motor_id] = MotorMode(mode_val)
                except Exception as e:
                    if self.on_error:
                        self.on_error(f"Mode update error: {e}")
                
                # Call main feedback callback
                if self.on_feedback:
                    try:
                        self.on_feedback(motor_id, feedback)
                    except Exception as e:
                        if self.on_error:
                            self.on_error(f"Main feedback callback error: {e}")
                
                # Call specific callback if provided
                if callback:
                    try:
                        callback(feedback)
                    except Exception as e:
                        if self.on_error:
                            self.on_error(f"Specific feedback callback error: {e}")
                
                return feedback
            return None
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Feedback request error: {e}")
            return None
    
    def stop(self, motor_id: int, callback: Optional[Callable] = None):
        """Emergency stop - bypasses queue for immediate response"""
        return self._emergency_stop_direct(motor_id, callback)
    
    def _emergency_stop_direct(self, motor_id: int, callback: Optional[Callable] = None) -> bool:
        """Direct emergency stop - bypasses all queuing and clears all queues"""
        try:
            # FIRST: Clear all pending commands for this motor and empty priority queue
            with self.command_lock:
                # Clear latest commands for this motor
                keys_to_remove = [k for k in self.latest_commands.keys() if k[0] == motor_id]
                for key in keys_to_remove:
                    del self.latest_commands[key]
                    self.commands_dropped += 1
            
            # Empty the priority queue of any remaining commands for this motor
            temp_queue = []
            while not self.command_queue.empty():
                try:
                    priority, cmd = self.command_queue.get_nowait()
                    if cmd.motor_id != motor_id:
                        temp_queue.append((priority, cmd))  # Keep commands for other motors
                    else:
                        self.commands_dropped += 1  # Drop commands for this motor
                except queue.Empty:
                    break
            
            # Put back commands for other motors
            for item in temp_queue:
                self.command_queue.put(item)
            
            # NOW: Execute emergency stop immediately
            success1 = self.motor.set_mode(motor_id, MotorMode.VELOCITY)
            success2 = self.motor.set_velocity(motor_id, 0)
            
            success = success1 and success2
            
            if success:
                self.current_mode[motor_id] = MotorMode.VELOCITY
                self.commands_processed += 1
            else:
                self.commands_failed += 1
            
            # Call callback if provided
            if callback:
                try:
                    callback(success)
                except Exception as e:
                    if self.on_error:
                        self.on_error(f"Emergency stop callback error: {e}")
            
            return success
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Emergency stop error: {e}")
            self.commands_failed += 1
            return False
    
    def enable(self, motor_id: int, callback: Optional[Callable] = None):
        """Queue enable command"""
        cmd = MotorCommand(CommandType.ENABLE, motor_id, None, callback)
        self._queue_command(cmd)
    
    def disable(self, motor_id: int, callback: Optional[Callable] = None):
        """Queue disable command"""
        cmd = MotorCommand(CommandType.DISABLE, motor_id, None, callback)
        self._queue_command(cmd)
    
    def set_motor_id(self, old_id: int, new_id: int, callback: Optional[Callable] = None) -> bool:
        """Set motor ID (change motor's ID from old_id to new_id)"""
        if not self.motor or not self.is_connected:
            return False
        
        try:
            # Call the underlying DDSM115 method directly (this is a synchronous operation)
            result = self.motor.set_motor_id(old_id, new_id)
            if callback:
                callback(result)
            return result
        except Exception as e:
            print(f"Error setting motor ID: {e}")
            if callback:
                callback(False)
            return False
    
    def get_last_feedback(self, motor_id: int) -> Optional[MotorFeedback]:
        """Get last feedback for motor"""
        return self.last_feedback.get(motor_id)
    
    def get_stats(self) -> dict:
        """Get processing statistics"""
        total = self.commands_processed + self.commands_failed
        success_rate = (self.commands_processed / total * 100) if total > 0 else 0
        
        with self.command_lock:
            pending_commands = len(self.latest_commands)
        
        return {
            'commands_processed': self.commands_processed,
            'commands_failed': self.commands_failed,
            'commands_dropped': self.commands_dropped,
            'success_rate': success_rate,
            'feedback_count': self.feedback_count,
            'queue_size': self.command_queue.qsize(),
            'pending_commands': pending_commands
        }
    
    def _queue_command(self, cmd: MotorCommand):
        """Add command to queue, replacing any existing command of the same type"""
        with self.command_lock:
            # Key for tracking latest commands (motor_id, command_type)
            key = (cmd.motor_id, cmd.command_type)
            
            # If there's already a command of this type, replace it (don't queue duplicate types)
            if key in self.latest_commands:
                self.commands_dropped += 1
            
            # Store as latest command
            self.latest_commands[key] = cmd
            
            # For high priority commands (stop, emergency), also add directly to queue
            if cmd.priority >= 3:
                priority = (-cmd.priority, cmd.timestamp)
                self.command_queue.put((priority, cmd))
    
    def _command_worker(self):
        """Main command processing worker with robust exception handling"""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.running:
            try:
                cmd = None
                
                # First check for high priority commands in queue
                try:
                    priority, cmd = self.command_queue.get_nowait()
                except queue.Empty:
                    pass
                except Exception as e:
                    if self.on_error:
                        self.on_error(f"Queue access error: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        if self.on_error:
                            self.on_error("Too many consecutive queue errors, pausing worker")
                        time.sleep(1.0)
                        consecutive_errors = 0
                    continue
                
                # If no high priority command, get latest command from each type
                if cmd is None:
                    try:
                        with self.command_lock:
                            if self.latest_commands:
                                # Get the oldest unprocessed command
                                oldest_key = min(self.latest_commands.keys(), 
                                               key=lambda k: self.latest_commands[k].timestamp)
                                cmd = self.latest_commands.pop(oldest_key)
                    except Exception as e:
                        if self.on_error:
                            self.on_error(f"Latest commands access error: {e}")
                        consecutive_errors += 1
                        continue
                
                if cmd is None:
                    time.sleep(0.01)  # 100Hz when no commands
                    consecutive_errors = 0  # Reset error counter when idle
                    continue
                
                # Rate limiting
                try:
                    now = time.time()
                    elapsed = now - self.last_command_time
                    if elapsed < self.min_command_interval:
                        time.sleep(self.min_command_interval - elapsed)
                except Exception as e:
                    if self.on_error:
                        self.on_error(f"Rate limiting error: {e}")
                    # Continue without rate limiting
                
                # Process command
                try:
                    success = self._execute_command(cmd)
                    consecutive_errors = 0  # Reset error counter on successful command processing
                except Exception as e:
                    if self.on_error:
                        self.on_error(f"Command execution error: {e}")
                    success = False
                    consecutive_errors += 1
                
                if success:
                    self.commands_processed += 1
                    # Notify GUI that a command was sent
                    if self.on_command_sent:
                        try:
                            self.on_command_sent()
                        except Exception as e:
                            if self.on_error:
                                self.on_error(f"Command sent callback error: {e}")
                else:
                    self.commands_failed += 1
                
                # Call callback if provided
                if cmd and cmd.callback:
                    try:
                        cmd.callback(success)
                    except Exception as e:
                        if self.on_error:
                            self.on_error(f"Callback error: {e}")
                
                try:
                    self.last_command_time = time.time()
                except Exception:
                    pass  # Ignore time errors
                
                # Add small delay after command to allow feedback requests
                try:
                    time.sleep(0.02)  # 20ms pause to allow feedback worker to run
                except Exception:
                    pass  # Ignore sleep errors
                
                # If too many consecutive errors, pause longer
                if consecutive_errors >= max_consecutive_errors:
                    if self.on_error:
                        self.on_error("Too many consecutive errors, pausing command worker")
                    time.sleep(1.0)
                    consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                if self.on_error:
                    self.on_error(f"Command worker critical error: {e}")
                
                # Progressive backoff on errors
                if consecutive_errors < 5:
                    time.sleep(0.1)
                elif consecutive_errors < 10:
                    time.sleep(0.5)
                else:
                    time.sleep(1.0)
                    consecutive_errors = 0  # Reset after long pause
    
    def _execute_command(self, cmd: MotorCommand) -> bool:
        """Execute individual command"""
        try:
            if cmd.command_type == CommandType.SET_VELOCITY:
                # Auto-switch to velocity mode if needed
                if self.current_mode.get(cmd.motor_id) != MotorMode.VELOCITY:
                    if not self._switch_mode_sync(cmd.motor_id, MotorMode.VELOCITY):
                        return False
                return self.motor.set_velocity(cmd.motor_id, cmd.value)
            
            elif cmd.command_type == CommandType.SET_CURRENT:
                # Auto-switch to current mode if needed
                if self.current_mode.get(cmd.motor_id) != MotorMode.CURRENT:
                    if not self._switch_mode_sync(cmd.motor_id, MotorMode.CURRENT):
                        return False
                # Use auto_switch_mode=False to prevent double mode switching
                return self.motor.set_current(cmd.motor_id, cmd.value, auto_switch_mode=False)
            
            elif cmd.command_type == CommandType.SET_POSITION:
                current_mode = self.current_mode.get(cmd.motor_id)
                
                # If already in position mode, send command directly
                if current_mode == MotorMode.POSITION:
                    return self.motor.set_position(cmd.motor_id, cmd.value)
                
                # If switching from velocity/current mode to position mode, check velocity
                if current_mode in [MotorMode.VELOCITY, MotorMode.CURRENT]:
                    feedback = self.last_feedback.get(cmd.motor_id)
                    if feedback and abs(feedback.velocity) >= 10:
                        # Need to stop motor first - send velocity 0, then position command
                        if not self._switch_mode_sync(cmd.motor_id, MotorMode.VELOCITY):
                            return False
                        if not self.motor.set_velocity(cmd.motor_id, 0):
                            return False
                        # Wait a moment for motor to slow down
                        time.sleep(0.2)
                
                # Now switch to position mode and send command
                if not self._switch_mode_sync(cmd.motor_id, MotorMode.POSITION):
                    return False
                return self.motor.set_position(cmd.motor_id, cmd.value)
            
            elif cmd.command_type == CommandType.SET_MODE:
                return self._switch_mode_sync(cmd.motor_id, cmd.value)
            
            elif cmd.command_type == CommandType.REQUEST_FEEDBACK:
                # Feedback requests now bypass the queue and execute immediately
                # This case should not occur anymore
                return True
            
            elif cmd.command_type == CommandType.STOP:
                # This should not happen since stop() bypasses the queue
                # But handle it just in case
                return self._emergency_stop_direct(cmd.motor_id, cmd.callback)
            
            elif cmd.command_type == CommandType.ENABLE:
                return self.motor.enable(cmd.motor_id)
            
            elif cmd.command_type == CommandType.DISABLE:
                return self.motor.disable(cmd.motor_id)
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"Command execution error: {e}")
            return False
        
        return False
    
    def _switch_mode_sync(self, motor_id: int, mode: MotorMode) -> bool:
        """Switch mode with minimal blocking"""
        if not self.motor.set_mode(motor_id, mode):
            return False
        
        # Brief delay for mode switch to take effect (much shorter)
        time.sleep(0.01)  # 10ms instead of 100ms
        
        # Optimistic assumption - mode switch usually works
        # The feedback worker will verify mode in its normal operation
        self.current_mode[motor_id] = mode
        
        return True
    
    
    def _feedback_worker(self):
        """Continuous feedback monitoring with robust exception handling"""
        last_feedback_time = {}
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.running:
            try:
                # Request feedback for all registered motors (including those with None mode)
                motor_ids = None
                try:
                    motor_ids = list(self.current_mode.keys())
                except Exception as e:
                    if self.on_error:
                        self.on_error(f"Motor list access error: {e}")
                    consecutive_errors += 1
                    time.sleep(0.1)
                    continue
                
                if not motor_ids:
                    time.sleep(0.1)  # No motors registered yet
                    consecutive_errors = 0
                    continue
                
                for motor_id in motor_ids:
                    if not self.running:  # Check if we should stop
                        break
                        
                    try:
                        now = time.time()
                        last_time = last_feedback_time.get(motor_id, 0)
                        
                        # Request feedback every 50ms per motor
                        if now - last_time >= 0.05:
                            self.request_feedback(motor_id)
                            last_feedback_time[motor_id] = now
                            consecutive_errors = 0  # Reset on successful feedback
                            
                    except Exception as e:
                        consecutive_errors += 1
                        if self.on_error:
                            self.on_error(f"Feedback request error for motor {motor_id}: {e}")
                        
                        # Don't break the loop for single motor errors
                        continue
                
                try:
                    time.sleep(0.01)  # 100Hz loop
                except Exception:
                    pass  # Ignore sleep errors
                
                # If too many consecutive errors, pause longer
                if consecutive_errors >= max_consecutive_errors:
                    if self.on_error:
                        self.on_error("Too many consecutive feedback errors, pausing feedback worker")
                    time.sleep(1.0)
                    consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                if self.on_error:
                    self.on_error(f"Feedback worker critical error: {e}")
                
                # Progressive backoff on errors
                if consecutive_errors < 5:
                    time.sleep(0.1)
                elif consecutive_errors < 10:
                    time.sleep(0.5)
                else:
                    time.sleep(1.0)
                    consecutive_errors = 0  # Reset after long pause