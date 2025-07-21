#!/usr/bin/env python3
"""
Test the command queue system under extreme stress
"""

import time
import random
import threading
from motor_command_queue import MotorCommandQueue, MotorMode

class CommandQueueStressTest:
    def __init__(self):
        self.queue = MotorCommandQueue("/dev/ttyUSB0")
        self.motor_id = None
        self.test_running = False
        self.commands_sent = 0
        
    def setup(self):
        """Setup the command queue system"""
        if not self.queue.connect():
            print("❌ Failed to connect")
            return False
        
        motors = self.queue.scan_motors(1, 10)
        if not motors:
            print("❌ No motors found")
            return False
        
        self.motor_id = motors[0]
        print(f"✅ Using motor ID {self.motor_id}")
        
        # Setup callbacks
        self.queue.on_feedback = self._on_feedback
        self.queue.on_error = self._on_error
        
        return True
    
    def _on_feedback(self, motor_id, feedback):
        """Handle feedback updates"""
        pass  # Just receive feedback silently
    
    def _on_error(self, error):
        """Handle errors"""
        print(f"⚠️ {error}")
    
    def chaos_sender(self, thread_id):
        """Send random commands rapidly"""
        print(f"🎯 Chaos sender {thread_id} starting...")
        
        while self.test_running:
            try:
                # Random command type
                cmd_type = random.choice(['velocity', 'current', 'position', 'mode', 'stop'])
                
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
                
                elif cmd_type == 'stop':
                    self.queue.stop(self.motor_id)
                
                self.commands_sent += 1
                
                # Very rapid sending
                time.sleep(random.uniform(0.001, 0.02))
                
            except Exception as e:
                print(f"Chaos sender {thread_id} error: {e}")
                time.sleep(0.1)
    
    def run_stress_test(self, duration=30, num_senders=5):
        """Run stress test with multiple command senders"""
        print("🚨 COMMAND QUEUE STRESS TEST")
        print("=" * 50)
        print(f"Duration: {duration} seconds")
        print(f"Concurrent senders: {num_senders}")
        print("=" * 50)
        
        if not self.setup():
            return False
        
        self.test_running = True
        start_time = time.time()
        
        # Start multiple chaos senders
        threads = []
        for i in range(num_senders):
            thread = threading.Thread(target=self.chaos_sender, args=(i,), daemon=True)
            threads.append(thread)
            thread.start()
        
        try:
            # Monitor progress
            last_stats_time = start_time
            while time.time() - start_time < duration:
                time.sleep(1)
                
                # Print stats every 5 seconds
                if time.time() - last_stats_time >= 5:
                    elapsed = int(time.time() - start_time)
                    stats = self.queue.get_stats()
                    
                    print(f"⏱️ {elapsed}s:")
                    print(f"  Commands sent: {self.commands_sent}")
                    print(f"  Commands processed: {stats['commands_processed']}")
                    print(f"  Commands failed: {stats['commands_failed']}")
                    print(f"  Success rate: {stats['success_rate']:.1f}%")
                    print(f"  Queue size: {stats['queue_size']}")
                    print(f"  Feedback count: {stats['feedback_count']}")
                    
                    last_stats_time = time.time()
        
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted")
        
        self.test_running = False
        
        # Final stats
        final_stats = self.queue.get_stats()
        
        print("\n" + "=" * 50)
        print("📊 FINAL RESULTS")
        print("=" * 50)
        print(f"Test duration: {time.time() - start_time:.1f}s")
        print(f"Commands sent: {self.commands_sent}")
        print(f"Commands processed: {final_stats['commands_processed']}")
        print(f"Commands failed: {final_stats['commands_failed']}")
        print(f"Success rate: {final_stats['success_rate']:.1f}%")
        print(f"Final queue size: {final_stats['queue_size']}")
        print(f"Feedback updates: {final_stats['feedback_count']}")
        
        # Performance analysis
        commands_per_sec = self.commands_sent / (time.time() - start_time)
        processed_per_sec = final_stats['commands_processed'] / (time.time() - start_time)
        
        print(f"\nPerformance:")
        print(f"Commands/sec sent: {commands_per_sec:.1f}")
        print(f"Commands/sec processed: {processed_per_sec:.1f}")
        
        if final_stats['success_rate'] >= 95:
            print("✅ EXCELLENT - Command queue handled stress very well")
        elif final_stats['success_rate'] >= 85:
            print("✅ GOOD - Command queue performed well under stress")
        elif final_stats['success_rate'] >= 70:
            print("⚠️ MODERATE - Some issues under extreme load")
        else:
            print("❌ POOR - Command queue struggled with load")
        
        if final_stats['queue_size'] > 100:
            print("⚠️ Large queue backlog - consider faster processing")
        
        self.queue.disconnect()
        return True

def main():
    print("🔥 Command Queue Stress Tester")
    print("Tests the new single-point command system")
    
    duration = int(input("Test duration (seconds, default 20): ") or "20")
    senders = int(input("Number of concurrent command senders (default 3): ") or "3")
    
    tester = CommandQueueStressTest()
    tester.run_stress_test(duration, senders)

if __name__ == "__main__":
    main()