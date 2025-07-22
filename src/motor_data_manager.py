"""
Motor Data Manager - Centralized motor communication and data distribution
"""

import threading
import queue
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Import existing motor classes
from ddsm115 import DDSM115, MotorMode, MotorFeedback


class DataEventType(Enum):
    """Types of data events"""
    MOTOR_FEEDBACK = "motor_feedback"
    MOTOR_STATUS_CHANGE = "motor_status_change"
    MOTOR_ERROR = "motor_error"
    MOTOR_CONNECTED = "motor_connected" 
    MOTOR_DISCONNECTED = "motor_disconnected"
    COMMAND_SENT = "command_sent"
    COMMAND_FAILED = "command_failed"


@dataclass
class DataEvent:
    """Data event that gets distributed to listeners"""
    event_type: DataEventType
    motor_id: int
    timestamp: float
    data: Any
    source: str = "motor_data_manager"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return asdict(self)


class MotorDataListener:
    """Base class for motor data listeners"""
    
    def __init__(self, name: str, queue_size: int = 100):
        self.name = name
        self.data_queue = queue.Queue(maxsize=queue_size)
        self.active = True
        self.filter_motor_ids: Optional[List[int]] = None
        self.filter_event_types: Optional[List[DataEventType]] = None
    
    def set_motor_filter(self, motor_ids: List[int]):
        """Filter to only receive data from specific motor IDs"""
        self.filter_motor_ids = motor_ids
    
    def set_event_filter(self, event_types: List[DataEventType]):
        """Filter to only receive specific event types"""
        self.filter_event_types = event_types
    
    def should_receive_event(self, event: DataEvent) -> bool:
        """Check if this listener should receive the event"""
        if not self.active:
            return False
        
        if self.filter_motor_ids and event.motor_id not in self.filter_motor_ids:
            return False
        
        if self.filter_event_types and event.event_type not in self.filter_event_types:
            return False
        
        return True
    
    def put_event(self, event: DataEvent) -> bool:
        """Put event in queue, return False if queue is full"""
        try:
            self.data_queue.put_nowait(event)
            return True
        except queue.Full:
            return False
    
    def get_event(self, timeout: Optional[float] = None) -> Optional[DataEvent]:
        """Get next event from queue"""
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_events(self) -> List[DataEvent]:
        """Get all pending events from queue"""
        events = []
        while True:
            try:
                events.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return events


class MotorDataManager:
    """Centralized motor data management and distribution system"""
    
    def __init__(self, port: str = "/dev/ttyUSB0"):
        self.port = port
        self.motor_controller: Optional[DDSM115] = None
        self.listeners: Dict[str, MotorDataListener] = {}
        
        # Motor state tracking
        self.connected_motors: Dict[int, bool] = {}
        self.motor_status: Dict[int, MotorFeedback] = {}
        self.last_feedback_time: Dict[int, float] = {}
        
        # Control
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.distribution_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'events_distributed': 0,
            'commands_sent': 0,
            'feedback_received': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        self._lock = threading.RLock()
    
    def connect(self) -> bool:
        """Connect to motor controller"""
        try:
            self.motor_controller = DDSM115(self.port)
            if self.motor_controller.connect():
                self.running = True
                self.start_monitoring()
                self._broadcast_event(DataEventType.MOTOR_CONNECTED, 0, {"port": self.port})
                return True
        except Exception as e:
            self._broadcast_event(DataEventType.MOTOR_ERROR, 0, {"error": str(e)})
        return False
    
    def disconnect(self):
        """Disconnect from motor controller"""
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        
        if self.motor_controller:
            self.motor_controller.disconnect()
            self.motor_controller = None
        
        self._broadcast_event(DataEventType.MOTOR_DISCONNECTED, 0, {"port": self.port})
    
    def register_listener(self, listener: MotorDataListener) -> bool:
        """Register a data listener"""
        with self._lock:
            if listener.name in self.listeners:
                return False
            self.listeners[listener.name] = listener
            return True
    
    def unregister_listener(self, name: str) -> bool:
        """Unregister a data listener"""
        with self._lock:
            if name in self.listeners:
                self.listeners[name].active = False
                del self.listeners[name]
                return True
            return False
    
    def get_listener(self, name: str) -> Optional[MotorDataListener]:
        """Get a registered listener"""
        with self._lock:
            return self.listeners.get(name)
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running and self.motor_controller:
            try:
                # Monitor all known motors (could be extended to scan for new ones)
                for motor_id in range(1, 11):  # Monitor motors 1-10
                    if not self.running:
                        break
                    
                    try:
                        feedback = self.motor_controller.request_feedback(motor_id)
                        if feedback:
                            self._handle_feedback(motor_id, feedback)
                        else:
                            self._handle_no_response(motor_id)
                    except Exception as e:
                        self._broadcast_event(DataEventType.MOTOR_ERROR, motor_id, {"error": str(e)})
                
                time.sleep(0.1)  # 100ms polling rate
                
            except Exception as e:
                self._broadcast_event(DataEventType.MOTOR_ERROR, 0, {"error": f"Monitor loop error: {e}"})
                time.sleep(1.0)  # Longer delay on error
    
    def _handle_feedback(self, motor_id: int, feedback: MotorFeedback):
        """Handle received motor feedback"""
        with self._lock:
            # Update tracking
            self.connected_motors[motor_id] = True
            self.motor_status[motor_id] = feedback
            self.last_feedback_time[motor_id] = time.time()
            self.stats['feedback_received'] += 1
            
            # Broadcast feedback event
            self._broadcast_event(DataEventType.MOTOR_FEEDBACK, motor_id, {
                'feedback': feedback,
                'velocity': feedback.velocity,
                'position': feedback.position,
                'torque': feedback.torque,
                'temperature': feedback.temperature,
                'raw_data': feedback.raw_data
            })
    
    def _handle_no_response(self, motor_id: int):
        """Handle when motor doesn't respond"""
        with self._lock:
            # Check if motor was previously connected
            was_connected = self.connected_motors.get(motor_id, False)
            
            if was_connected:
                # Motor went offline
                self.connected_motors[motor_id] = False
                self._broadcast_event(DataEventType.MOTOR_STATUS_CHANGE, motor_id, {
                    'status': 'disconnected',
                    'last_seen': self.last_feedback_time.get(motor_id, 0)
                })
    
    def _broadcast_event(self, event_type: DataEventType, motor_id: int, data: Any):
        """Broadcast event to all appropriate listeners"""
        event = DataEvent(
            event_type=event_type,
            motor_id=motor_id,
            timestamp=time.time(),
            data=data
        )
        
        distributed_count = 0
        with self._lock:
            for listener in self.listeners.values():
                if listener.should_receive_event(event):
                    if listener.put_event(event):
                        distributed_count += 1
        
        self.stats['events_distributed'] += distributed_count
    
    # Motor control methods - these will distribute command events
    def set_velocity(self, motor_id: int, velocity: float) -> bool:
        """Set motor velocity"""
        if not self.motor_controller:
            return False
        
        try:
            result = self.motor_controller.set_velocity(motor_id, velocity)
            self.stats['commands_sent'] += 1
            self._broadcast_event(DataEventType.COMMAND_SENT, motor_id, {
                'command': 'set_velocity',
                'value': velocity,
                'success': result
            })
            return result
        except Exception as e:
            self._broadcast_event(DataEventType.COMMAND_FAILED, motor_id, {
                'command': 'set_velocity',
                'value': velocity,
                'error': str(e)
            })
            return False
    
    def set_position(self, motor_id: int, position: float) -> bool:
        """Set motor position"""
        if not self.motor_controller:
            return False
        
        try:
            result = self.motor_controller.set_position(motor_id, position)
            self.stats['commands_sent'] += 1
            self._broadcast_event(DataEventType.COMMAND_SENT, motor_id, {
                'command': 'set_position',
                'value': position,
                'success': result
            })
            return result
        except Exception as e:
            self._broadcast_event(DataEventType.COMMAND_FAILED, motor_id, {
                'command': 'set_position',
                'value': position,
                'error': str(e)
            })
            return False
    
    def set_current(self, motor_id: int, current: float) -> bool:
        """Set motor current"""
        if not self.motor_controller:
            return False
        
        try:
            result = self.motor_controller.set_current(motor_id, current)
            self.stats['commands_sent'] += 1
            self._broadcast_event(DataEventType.COMMAND_SENT, motor_id, {
                'command': 'set_current',
                'value': current,
                'success': result
            })
            return result
        except Exception as e:
            self._broadcast_event(DataEventType.COMMAND_FAILED, motor_id, {
                'command': 'set_current',
                'value': current,
                'error': str(e)
            })
            return False
    
    def stop_motor(self, motor_id: int) -> bool:
        """Stop motor"""
        if not self.motor_controller:
            return False
        
        try:
            result = self.motor_controller.stop(motor_id)
            self.stats['commands_sent'] += 1
            self._broadcast_event(DataEventType.COMMAND_SENT, motor_id, {
                'command': 'stop',
                'success': result
            })
            return result
        except Exception as e:
            self._broadcast_event(DataEventType.COMMAND_FAILED, motor_id, {
                'command': 'stop',
                'error': str(e)
            })
            return False
    
    def enable_motor(self, motor_id: int) -> bool:
        """Enable motor"""
        if not self.motor_controller:
            return False
        
        try:
            result = self.motor_controller.enable(motor_id)
            self.stats['commands_sent'] += 1
            self._broadcast_event(DataEventType.COMMAND_SENT, motor_id, {
                'command': 'enable',
                'success': result
            })
            return result
        except Exception as e:
            self._broadcast_event(DataEventType.COMMAND_FAILED, motor_id, {
                'command': 'enable',
                'error': str(e)
            })
            return False
    
    def disable_motor(self, motor_id: int) -> bool:
        """Disable motor"""
        if not self.motor_controller:
            return False
        
        try:
            result = self.motor_controller.disable(motor_id)
            self.stats['commands_sent'] += 1
            self._broadcast_event(DataEventType.COMMAND_SENT, motor_id, {
                'command': 'disable',
                'success': result
            })
            return result
        except Exception as e:
            self._broadcast_event(DataEventType.COMMAND_FAILED, motor_id, {
                'command': 'disable',
                'error': str(e)
            })
            return False
    
    def get_motor_status(self, motor_id: int) -> Optional[MotorFeedback]:
        """Get last known status for motor"""
        with self._lock:
            return self.motor_status.get(motor_id)
    
    def get_connected_motors(self) -> List[int]:
        """Get list of currently connected motor IDs"""
        with self._lock:
            return [motor_id for motor_id, connected in self.connected_motors.items() if connected]
    
    def get_stats(self) -> dict:
        """Get statistics"""
        with self._lock:
            stats = self.stats.copy()
            stats['uptime'] = time.time() - stats['start_time']
            stats['active_listeners'] = len([l for l in self.listeners.values() if l.active])
            stats['connected_motors'] = len(self.get_connected_motors())
            return stats


# Convenience listener classes for common use cases
class GraphDataListener(MotorDataListener):
    """Specialized listener for graph data"""
    
    def __init__(self, queue_size: int = 200):
        super().__init__("graph", queue_size)
        self.set_event_filter([DataEventType.MOTOR_FEEDBACK])
        
        # Graph-specific data storage
        from collections import deque
        self.plot_data = {}  # motor_id -> {'time': deque, 'velocity': deque, ...}
        self.max_points = 200
    
    def process_events(self):
        """Process all pending events and update graph data"""
        events = self.get_all_events()
        
        for event in events:
            if event.event_type == DataEventType.MOTOR_FEEDBACK:
                motor_id = event.motor_id
                
                # Initialize data storage for new motor
                if motor_id not in self.plot_data:
                    from collections import deque
                    self.plot_data[motor_id] = {
                        'time': deque(maxlen=self.max_points),
                        'velocity': deque(maxlen=self.max_points),
                        'position': deque(maxlen=self.max_points),
                        'torque': deque(maxlen=self.max_points),
                        'temperature': deque(maxlen=self.max_points)
                    }
                
                # Add new data point
                data = event.data
                self.plot_data[motor_id]['time'].append(event.timestamp)
                self.plot_data[motor_id]['velocity'].append(data.get('velocity', 0))
                self.plot_data[motor_id]['position'].append(data.get('position', 0))
                self.plot_data[motor_id]['torque'].append(data.get('torque', 0))
                self.plot_data[motor_id]['temperature'].append(data.get('temperature', 0))
    
    def get_plot_data(self, motor_id: int) -> Optional[dict]:
        """Get plot data for specific motor"""
        return self.plot_data.get(motor_id)
    
    def clear_data(self, motor_id: Optional[int] = None):
        """Clear plot data for specific motor or all motors"""
        if motor_id is None:
            self.plot_data.clear()
        elif motor_id in self.plot_data:
            for deque_data in self.plot_data[motor_id].values():
                deque_data.clear()


class UIStatusListener(MotorDataListener):
    """Specialized listener for UI status updates"""
    
    def __init__(self):
        super().__init__("ui_status", 50)
        self.set_event_filter([
            DataEventType.MOTOR_FEEDBACK,
            DataEventType.MOTOR_STATUS_CHANGE,
            DataEventType.COMMAND_SENT,
            DataEventType.COMMAND_FAILED
        ])
        
        self.latest_status = {}  # motor_id -> latest status info
    
    def get_latest_status(self, motor_id: int) -> Optional[dict]:
        """Get latest status for motor"""
        return self.latest_status.get(motor_id)
    
    def process_events(self):
        """Process events and update status"""
        events = self.get_all_events()
        
        for event in events:
            motor_id = event.motor_id
            
            if motor_id not in self.latest_status:
                self.latest_status[motor_id] = {}
            
            if event.event_type == DataEventType.MOTOR_FEEDBACK:
                data = event.data
                self.latest_status[motor_id].update({
                    'velocity': data.get('velocity', 0),
                    'position': data.get('position', 0),
                    'torque': data.get('torque', 0),
                    'temperature': data.get('temperature', 0),
                    'last_update': event.timestamp,
                    'connected': True
                })
            
            elif event.event_type == DataEventType.MOTOR_STATUS_CHANGE:
                self.latest_status[motor_id]['connected'] = event.data.get('status') == 'connected'
            
            elif event.event_type in [DataEventType.COMMAND_SENT, DataEventType.COMMAND_FAILED]:
                self.latest_status[motor_id]['last_command'] = event.data.get('command')
                self.latest_status[motor_id]['last_command_success'] = event.event_type == DataEventType.COMMAND_SENT