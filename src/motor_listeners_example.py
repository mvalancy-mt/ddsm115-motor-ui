"""
Example implementations of motor data listeners
"""

import time
import threading
from motor_data_manager import MotorDataManager, MotorDataListener, DataEventType, GraphDataListener, UIStatusListener


class LoggingListener(MotorDataListener):
    """Example listener that logs all motor events to file"""
    
    def __init__(self, log_file: str = "motor_events.log"):
        super().__init__("logger", 1000)
        self.log_file = log_file
        self.processing_thread = None
        self.start_processing()
    
    def start_processing(self):
        """Start background processing thread"""
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
    
    def _process_loop(self):
        """Background processing loop"""
        with open(self.log_file, 'a') as f:
            while self.active:
                event = self.get_event(timeout=1.0)
                if event:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp))
                    log_entry = f"[{timestamp}] Motor {event.motor_id}: {event.event_type.value} - {event.data}\n"
                    f.write(log_entry)
                    f.flush()


class AlertListener(MotorDataListener):
    """Example listener that monitors for alerts and warnings"""
    
    def __init__(self, callback_func=None):
        super().__init__("alerts", 100)
        self.callback_func = callback_func
        self.alert_thresholds = {
            'temperature': 70,  # °C
            'torque': 4.0,      # A
            'velocity': 1000    # RPM
        }
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
    
    def _process_loop(self):
        """Background processing for alerts"""
        while self.active:
            event = self.get_event(timeout=1.0)
            if event and event.event_type == DataEventType.MOTOR_FEEDBACK:
                self._check_alerts(event)
    
    def _check_alerts(self, event):
        """Check for alert conditions"""
        data = event.data
        motor_id = event.motor_id
        alerts = []
        
        # Temperature alert
        temp = data.get('temperature', 0)
        if temp > self.alert_thresholds['temperature']:
            alerts.append(f"High temperature: {temp}°C")
        
        # Torque alert
        torque = abs(data.get('torque', 0))
        if torque > self.alert_thresholds['torque']:
            alerts.append(f"High torque: {torque}A")
        
        # Velocity alert
        velocity = abs(data.get('velocity', 0))
        if velocity > self.alert_thresholds['velocity']:
            alerts.append(f"High velocity: {velocity}RPM")
        
        # Trigger callback if alerts found
        if alerts and self.callback_func:
            self.callback_func(motor_id, alerts)


class DataRecorder(MotorDataListener):
    """Example listener that records motor data to CSV"""
    
    def __init__(self, csv_file: str = "motor_data.csv"):
        super().__init__("recorder", 1000)
        self.csv_file = csv_file
        self.recording = False
        self._init_csv_file()
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
    
    def _init_csv_file(self):
        """Initialize CSV file with headers"""
        try:
            with open(self.csv_file, 'w') as f:
                f.write("timestamp,motor_id,velocity,position,torque,temperature\n")
        except Exception as e:
            print(f"Failed to initialize CSV file: {e}")
    
    def start_recording(self):
        """Start recording data"""
        self.recording = True
    
    def stop_recording(self):
        """Stop recording data"""
        self.recording = False
    
    def _process_loop(self):
        """Background processing for recording"""
        while self.active:
            event = self.get_event(timeout=1.0)
            if event and event.event_type == DataEventType.MOTOR_FEEDBACK and self.recording:
                self._record_data(event)
    
    def _record_data(self, event):
        """Record data to CSV"""
        try:
            data = event.data
            with open(self.csv_file, 'a') as f:
                line = f"{event.timestamp},{event.motor_id},{data.get('velocity', 0)},{data.get('position', 0)},{data.get('torque', 0)},{data.get('temperature', 0)}\n"
                f.write(line)
        except Exception as e:
            print(f"Failed to record data: {e}")


def demo_motor_data_manager():
    """Demonstration of the motor data manager system"""
    
    print("🚀 Motor Data Manager Demo")
    print("=" * 50)
    
    # Create manager
    manager = MotorDataManager("/dev/ttyUSB0")
    
    # Create listeners
    graph_listener = GraphDataListener()
    ui_listener = UIStatusListener()
    log_listener = LoggingListener("demo_motor.log")
    
    # Set up alert callback
    def alert_callback(motor_id, alerts):
        print(f"⚠️  ALERT Motor {motor_id}: {', '.join(alerts)}")
    
    alert_listener = AlertListener(alert_callback)
    recorder = DataRecorder("demo_data.csv")
    
    # Register listeners
    manager.register_listener(graph_listener)
    manager.register_listener(ui_listener)
    manager.register_listener(log_listener)
    manager.register_listener(alert_listener)
    manager.register_listener(recorder)
    
    print(f"📋 Registered {len(manager.listeners)} listeners")
    
    # Filter examples
    graph_listener.set_motor_filter([1, 2, 5])  # Graph only shows motors 1, 2, 5
    recorder.set_motor_filter([1])  # Record only motor 1
    
    try:
        # Connect (this would normally connect to real hardware)
        print("🔌 Connecting to motor controller...")
        if manager.connect():
            print("✅ Connected successfully")
            
            # Start recording
            recorder.start_recording()
            print("🎬 Started data recording")
            
            # Run for demo period
            print("📊 Running demo for 10 seconds...")
            time.sleep(10)
            
            # Show stats
            stats = manager.get_stats()
            print(f"\n📈 Statistics:")
            print(f"  Events distributed: {stats['events_distributed']}")
            print(f"  Commands sent: {stats['commands_sent']}")
            print(f"  Feedback received: {stats['feedback_received']}")
            print(f"  Connected motors: {stats['connected_motors']}")
            print(f"  Active listeners: {stats['active_listeners']}")
            
            # Show graph data for motor 1
            graph_data = graph_listener.get_plot_data(1)
            if graph_data:
                print(f"\n📊 Graph data for Motor 1:")
                print(f"  Data points: {len(graph_data['time'])}")
                if graph_data['velocity']:
                    print(f"  Latest velocity: {graph_data['velocity'][-1]:.1f} RPM")
                    print(f"  Latest position: {graph_data['position'][-1]:.1f}°")
            
            # Show UI status
            ui_status = ui_listener.get_latest_status(1)
            if ui_status:
                print(f"\n📱 UI Status for Motor 1:")
                print(f"  Connected: {ui_status.get('connected', False)}")
                print(f"  Velocity: {ui_status.get('velocity', 0):.1f} RPM")
                print(f"  Position: {ui_status.get('position', 0):.1f}°")
                print(f"  Torque: {ui_status.get('torque', 0):.2f} A")
            
        else:
            print("❌ Failed to connect")
    
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    
    finally:
        # Cleanup
        recorder.stop_recording()
        manager.disconnect()
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    demo_motor_data_manager()