#!/usr/bin/env python3
"""
GUI Diagnostic Tool - Run alongside the GUI to monitor performance issues
"""

import time
import threading
import psutil
import sys
from ddsm115 import DDSM115, MotorMode

class GUIDiagnostic:
    def __init__(self):
        self.monitoring = False
        self.motor = DDSM115(port="/dev/ttyUSB0", suppress_comm_errors=False)
        self.last_feedback_time = None
        self.feedback_intervals = []
        self.command_response_times = []
        
    def start_monitoring(self):
        """Start monitoring GUI performance"""
        print("🔧 Starting GUI Diagnostic Monitor")
        print("=" * 50)
        print("Run this alongside your GUI to monitor:")
        print("- Communication response times")
        print("- Memory usage")
        print("- Motor feedback consistency")
        print("- Mode switching performance")
        print("\nPress Ctrl+C to stop monitoring")
        print("=" * 50)
        
        # Connect to motor
        if not self.motor.connect():
            print("❌ Failed to connect to motor")
            return
        
        # Find motor
        motors = self.motor.scan_motors(1, 10)
        if not motors:
            print("❌ No motors found")
            return
        
        motor_id = motors[0]
        print(f"✅ Monitoring motor ID {motor_id}")
        
        self.monitoring = True
        
        # Start monitoring threads
        feedback_thread = threading.Thread(target=self._monitor_feedback, args=(motor_id,))
        performance_thread = threading.Thread(target=self._monitor_performance)
        
        feedback_thread.daemon = True
        performance_thread.daemon = True
        
        feedback_thread.start()
        performance_thread.start()
        
        try:
            # Main monitoring loop
            while self.monitoring:
                time.sleep(1)
                self._print_status()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping diagnostic monitor...")
            self.monitoring = False
            
        self.motor.disconnect()
        print("✅ Diagnostic complete")
    
    def _monitor_feedback(self, motor_id):
        """Monitor feedback response times"""
        while self.monitoring:
            try:
                start_time = time.time()
                feedback = self.motor.request_feedback(motor_id)
                response_time = time.time() - start_time
                
                if feedback:
                    # Track response times
                    self.command_response_times.append(response_time)
                    if len(self.command_response_times) > 100:
                        self.command_response_times.pop(0)
                    
                    # Track feedback intervals
                    now = time.time()
                    if self.last_feedback_time:
                        interval = now - self.last_feedback_time
                        self.feedback_intervals.append(interval)
                        if len(self.feedback_intervals) > 50:
                            self.feedback_intervals.pop(0)
                    
                    self.last_feedback_time = now
                
                time.sleep(0.1)  # 10Hz monitoring
                
            except Exception as e:
                print(f"⚠️ Feedback error: {e}")
                time.sleep(0.5)
    
    def _monitor_performance(self):
        """Monitor system performance"""
        while self.monitoring:
            try:
                # Monitor memory usage of current process
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                
                # Store performance data (you could expand this)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"⚠️ Performance monitoring error: {e}")
                time.sleep(5)
    
    def _print_status(self):
        """Print current diagnostic status"""
        # Clear previous line (for live updating)
        sys.stdout.write('\033[2K\033[1G')
        
        status_parts = []
        
        # Response time status
        if self.command_response_times:
            avg_response = sum(self.command_response_times) / len(self.command_response_times)
            max_response = max(self.command_response_times)
            
            if avg_response > 0.1:
                status_parts.append(f"❌ Slow response: {avg_response:.3f}s avg, {max_response:.3f}s max")
            elif max_response > 0.2:
                status_parts.append(f"⚠️ Variable response: {avg_response:.3f}s avg, {max_response:.3f}s max")
            else:
                status_parts.append(f"✅ Good response: {avg_response:.3f}s avg")
        
        # Feedback interval status
        if self.feedback_intervals:
            avg_interval = sum(self.feedback_intervals) / len(self.feedback_intervals)
            expected_interval = 0.1  # We request every 100ms
            
            if abs(avg_interval - expected_interval) > 0.05:
                status_parts.append(f"⚠️ Irregular feedback: {avg_interval:.3f}s interval")
            else:
                status_parts.append("✅ Consistent feedback")
        
        # Memory status
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb > 100:
                status_parts.append(f"⚠️ High memory: {memory_mb:.1f}MB")
            else:
                status_parts.append(f"✅ Memory OK: {memory_mb:.1f}MB")
        except:
            pass
        
        status_line = " | ".join(status_parts) if status_parts else "📊 Monitoring..."
        print(f"\r{status_line}", end="", flush=True)
    
    def test_mode_switching_speed(self):
        """Test how fast mode switching works"""
        print("\n🔄 Testing Mode Switching Speed")
        print("-" * 30)
        
        if not self.motor.connect():
            print("❌ Failed to connect")
            return
        
        motors = self.motor.scan_motors(1, 10)
        if not motors:
            print("❌ No motors found")
            return
        
        motor_id = motors[0]
        
        modes = [
            (MotorMode.VELOCITY, "Velocity"),
            (MotorMode.CURRENT, "Current"),
            (MotorMode.POSITION, "Position"),
            (MotorMode.VELOCITY, "Velocity")
        ]
        
        for mode_enum, mode_name in modes:
            start_time = time.time()
            
            # Switch mode
            success = self.motor.set_mode(motor_id, mode_enum)
            mode_switch_time = time.time() - start_time
            
            if success:
                # Verify mode switch
                time.sleep(0.1)  # Small delay
                feedback = self.motor.request_feedback(motor_id)
                if feedback:
                    actual_mode = feedback.raw_data[1] if len(feedback.raw_data) > 1 else -1
                    expected_mode = int(mode_enum)
                    
                    if actual_mode == expected_mode:
                        print(f"✅ {mode_name}: {mode_switch_time:.3f}s")
                    else:
                        print(f"❌ {mode_name}: Switch failed (got mode {actual_mode})")
                else:
                    print(f"⚠️ {mode_name}: No feedback after switch")
            else:
                print(f"❌ {mode_name}: Command failed")
            
            time.sleep(0.5)  # Wait between switches
        
        self.motor.disconnect()

def main():
    diagnostic = GUIDiagnostic()
    
    print("🔧 DDSM115 GUI Diagnostic Tool")
    print("\nChoose test mode:")
    print("1. Real-time monitoring (run alongside GUI)")
    print("2. Mode switching speed test")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\nStarting real-time monitoring...")
        print("Now open the GUI in another terminal and interact with sliders")
        diagnostic.start_monitoring()
    elif choice == "2":
        diagnostic.test_mode_switching_speed()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()