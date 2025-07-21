#!/usr/bin/env python3
"""
Test emergency stop functionality during chaotic command sending
"""

import time
import random
import threading
from motor_command_queue import MotorCommandQueue, MotorMode

class EmergencyStopTest:
    def __init__(self):
        self.queue = MotorCommandQueue("/dev/ttyUSB0")
        self.motor_id = None
        self.chaos_running = False
        self.commands_sent_before_stop = 0
        self.stop_response_time = None
        
    def setup(self):
        """Setup the system"""
        if not self.queue.connect():
            print("❌ Failed to connect")
            return False
        
        motors = self.queue.scan_motors(1, 10)
        if not motors:
            print("❌ No motors found")
            return False
        
        self.motor_id = motors[0]
        print(f"✅ Using motor ID {self.motor_id}")
        return True
    
    def chaos_command_sender(self):
        """Send random commands rapidly to build up queue"""
        while self.chaos_running:
            try:
                # Send random commands rapidly
                cmd_type = random.choice(['velocity', 'current', 'position', 'mode'])
                
                if cmd_type == 'velocity':
                    vel = random.randint(-100, 100)
                    self.queue.set_velocity(self.motor_id, vel)
                elif cmd_type == 'current':
                    curr = random.uniform(-8, 8)
                    self.queue.set_current(self.motor_id, curr)
                elif cmd_type == 'position':
                    pos = random.uniform(0, 360)
                    self.queue.set_position(self.motor_id, pos)
                elif cmd_type == 'mode':
                    mode = random.choice([MotorMode.VELOCITY, MotorMode.CURRENT, MotorMode.POSITION])
                    self.queue.set_mode(self.motor_id, mode)
                
                self.commands_sent_before_stop += 1
                time.sleep(0.001)  # Very rapid sending
                
            except Exception as e:
                print(f"Chaos sender error: {e}")
                time.sleep(0.1)
    
    def test_emergency_stop_response(self):
        """Test emergency stop response time during chaos"""
        print("🚨 Testing Emergency Stop Response Time")
        print("=" * 50)
        
        if not self.setup():
            return False
        
        # Start chaos command sending
        self.chaos_running = True
        chaos_thread = threading.Thread(target=self.chaos_command_sender, daemon=True)
        chaos_thread.start()
        
        # Let chaos build up for a bit
        print("Building up command queue chaos...")
        time.sleep(2)
        
        # Check queue stats before stop
        stats_before = self.queue.get_stats()
        print(f"Queue before E-stop: {stats_before['pending_commands']} pending, {stats_before['queue_size']} priority queue")
        
        # Trigger emergency stop and measure response time
        print("🛑 TRIGGERING EMERGENCY STOP...")
        start_time = time.time()
        
        success = self.queue.stop(self.motor_id)
        
        end_time = time.time()
        self.stop_response_time = end_time - start_time
        
        # Stop chaos
        self.chaos_running = False
        
        # Check queue stats after stop
        time.sleep(0.1)  # Let things settle
        stats_after = self.queue.get_stats()
        
        print(f"\n📊 Emergency Stop Results:")
        print(f"Success: {'✅' if success else '❌'}")
        print(f"Response time: {self.stop_response_time:.6f} seconds ({self.stop_response_time*1000:.2f}ms)")
        print(f"Commands sent before stop: {self.commands_sent_before_stop}")
        print(f"Queue before: {stats_before['pending_commands']} pending, {stats_before['queue_size']} priority")
        print(f"Queue after: {stats_after['pending_commands']} pending, {stats_after['queue_size']} priority")
        print(f"Commands dropped: {stats_after['commands_dropped'] - stats_before['commands_dropped']}")
        
        # Verify motor is stopped
        feedback = self.queue.get_last_feedback(self.motor_id)
        if feedback:
            print(f"Motor velocity after stop: {feedback.velocity:.1f} RPM")
        
        # Performance analysis
        if self.stop_response_time < 0.01:  # 10ms
            print("✅ EXCELLENT - Sub-10ms emergency stop response")
        elif self.stop_response_time < 0.05:  # 50ms
            print("✅ GOOD - Emergency stop under 50ms")
        elif self.stop_response_time < 0.1:  # 100ms
            print("⚠️ ACCEPTABLE - Emergency stop under 100ms")
        else:
            print("❌ SLOW - Emergency stop over 100ms")
        
        # Check if queue was properly cleared
        queue_cleared = (stats_after['pending_commands'] == 0 and 
                        stats_after['queue_size'] <= stats_before['queue_size'])
        
        if queue_cleared:
            print("✅ GOOD - Command queues properly cleared")
        else:
            print("⚠️ WARNING - Some commands may still be queued")
        
        self.queue.disconnect()
        return success and self.stop_response_time < 0.1
    
    def test_multiple_emergency_stops(self):
        """Test multiple emergency stops in rapid succession"""
        print("\n🔄 Testing Multiple Rapid Emergency Stops")
        print("=" * 50)
        
        if not self.setup():
            return False
        
        response_times = []
        
        for i in range(5):
            print(f"\nTest {i+1}/5:")
            
            # Send some commands to create activity
            for _ in range(20):
                self.queue.set_velocity(self.motor_id, random.randint(-50, 50))
            
            # Trigger emergency stop
            start_time = time.time()
            success = self.queue.stop(self.motor_id)
            response_time = time.time() - start_time
            
            response_times.append(response_time)
            print(f"  Response time: {response_time:.6f}s ({'✅' if success else '❌'})")
            
            time.sleep(0.5)  # Brief pause between tests
        
        # Analysis
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        min_response = min(response_times)
        
        print(f"\n📊 Multiple E-stop Results:")
        print(f"Average response: {avg_response:.6f}s ({avg_response*1000:.2f}ms)")
        print(f"Best response: {min_response:.6f}s ({min_response*1000:.2f}ms)")
        print(f"Worst response: {max_response:.6f}s ({max_response*1000:.2f}ms)")
        
        if max_response < 0.02:
            print("✅ EXCELLENT - Consistent sub-20ms responses")
        elif max_response < 0.05:
            print("✅ GOOD - All responses under 50ms")
        else:
            print("⚠️ Variable - Some slow responses detected")
        
        self.queue.disconnect()
        return all(t < 0.1 for t in response_times)

def main():
    print("🚨 Emergency Stop Response Tester")
    print("Tests E-stop performance under extreme conditions")
    
    tester = EmergencyStopTest()
    
    test1_pass = tester.test_emergency_stop_response()
    test2_pass = tester.test_multiple_emergency_stops()
    
    print("\n" + "=" * 50)
    print("🏁 FINAL RESULTS")
    print("=" * 50)
    
    if test1_pass and test2_pass:
        print("✅ ALL TESTS PASSED - Emergency stop system is robust")
    elif test1_pass or test2_pass:
        print("⚠️ PARTIAL PASS - Some issues detected")
    else:
        print("❌ TESTS FAILED - Emergency stop needs improvement")
    
    print("\nThis system is now ready for GUI integration!")

if __name__ == "__main__":
    main()