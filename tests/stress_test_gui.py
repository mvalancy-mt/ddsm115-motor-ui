#!/usr/bin/env python3
"""
Aggressive GUI stress test - simulate a kid mashing all controls randomly
"""

import time
import random
import threading
from ddsm115 import DDSM115, MotorMode

class GUIStressTest:
    def __init__(self):
        self.motor = DDSM115(port="/dev/ttyUSB0", suppress_comm_errors=False)
        self.motor_id = None
        self.test_running = False
        self.commands_sent = 0
        self.commands_failed = 0
        self.mode_switches = 0
        self.feedback_failures = 0
        
    def connect_motor(self):
        """Connect and find motor"""
        if not self.motor.connect():
            print("❌ Failed to connect")
            return False
        
        motors = self.motor.scan_motors(1, 10)
        if not motors:
            print("❌ No motors found")
            return False
        
        self.motor_id = motors[0]
        print(f"✅ Found motor ID {self.motor_id}")
        return True
    
    def random_slider_chaos(self):
        """Simulate crazy slider movements"""
        print("🎮 Starting Random Slider Chaos...")
        
        while self.test_running:
            try:
                # Random slider action
                action = random.choice([
                    'velocity_drag', 'velocity_jump', 
                    'current_drag', 'current_jump',
                    'position_drag', 'position_jump',
                    'mode_switch', 'rapid_commands'
                ])
                
                if action == 'velocity_drag':
                    # Simulate dragging velocity slider rapidly
                    start_vel = random.randint(-100, 100)
                    end_vel = random.randint(-100, 100)
                    steps = random.randint(3, 8)
                    
                    for i in range(steps):
                        vel = int(start_vel + (end_vel - start_vel) * i / steps)
                        self._send_velocity_command(vel)
                        time.sleep(random.uniform(0.01, 0.05))  # Very fast like slider drag
                
                elif action == 'velocity_jump':
                    # Sudden velocity changes (slider jumps)
                    vel = random.choice([-100, -50, 0, 50, 100])
                    self._send_velocity_command(vel)
                
                elif action == 'current_drag':
                    # Current slider chaos
                    start_curr = random.uniform(-8, 8)
                    end_curr = random.uniform(-8, 8)
                    steps = random.randint(2, 6)
                    
                    for i in range(steps):
                        curr = start_curr + (end_curr - start_curr) * i / steps
                        self._send_current_command(curr)
                        time.sleep(random.uniform(0.02, 0.06))
                
                elif action == 'current_jump':
                    curr = random.uniform(-8, 8)
                    self._send_current_command(curr)
                
                elif action == 'position_drag':
                    # Position slider movements
                    start_pos = random.uniform(0, 360)
                    end_pos = random.uniform(0, 360)
                    steps = random.randint(2, 5)
                    
                    for i in range(steps):
                        pos = start_pos + (end_pos - start_pos) * i / steps
                        self._send_position_command(pos)
                        time.sleep(random.uniform(0.05, 0.1))
                
                elif action == 'position_jump':
                    pos = random.uniform(0, 360)
                    self._send_position_command(pos)
                
                elif action == 'mode_switch':
                    # Random mode switching
                    mode = random.choice([MotorMode.VELOCITY, MotorMode.CURRENT, MotorMode.POSITION])
                    self._switch_mode(mode)
                
                elif action == 'rapid_commands':
                    # Send many commands very quickly
                    for _ in range(random.randint(5, 15)):
                        if random.choice([True, False]):
                            self._send_velocity_command(random.randint(-50, 50))
                        else:
                            self._send_current_command(random.uniform(-2, 2))
                        time.sleep(0.01)  # Very rapid
                
                # Random pause between actions
                time.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                print(f"⚠️ Chaos error: {e}")
                self.commands_failed += 1
                time.sleep(0.1)
    
    def button_masher(self):
        """Simulate mashing buttons repeatedly"""
        print("🔨 Starting Button Masher...")
        
        button_actions = [
            'stop', 'enable', 'disable', 'emergency_stop',
            'connect', 'disconnect'
        ]
        
        while self.test_running:
            try:
                action = random.choice(button_actions)
                
                if action == 'stop':
                    self._send_velocity_command(0)
                elif action == 'enable':
                    self.motor.enable(self.motor_id)
                elif action == 'disable':
                    self.motor.disable(self.motor_id)
                elif action == 'emergency_stop':
                    self._send_velocity_command(0)
                    self._send_current_command(0)
                # Skip connect/disconnect as they're too disruptive
                
                time.sleep(random.uniform(0.2, 0.8))
                
            except Exception as e:
                print(f"⚠️ Button masher error: {e}")
                time.sleep(0.5)
    
    def feedback_monitor(self):
        """Continuously monitor feedback to simulate graph updates"""
        print("📊 Starting Feedback Monitor...")
        
        feedback_count = 0
        last_print = time.time()
        
        while self.test_running:
            try:
                feedback = self.motor.request_feedback(self.motor_id)
                if feedback:
                    feedback_count += 1
                else:
                    self.feedback_failures += 1
                
                # Print status every 5 seconds
                now = time.time()
                if now - last_print > 5:
                    print(f"📈 Feedback: {feedback_count} success, {self.feedback_failures} failures")
                    last_print = now
                    feedback_count = 0
                    self.feedback_failures = 0
                
                time.sleep(0.05)  # 20Hz like the GUI
                
            except Exception as e:
                self.feedback_failures += 1
                time.sleep(0.1)
    
    def _send_velocity_command(self, velocity):
        """Send velocity command with error tracking"""
        try:
            if self.motor.set_velocity(self.motor_id, velocity):
                self.commands_sent += 1
            else:
                self.commands_failed += 1
        except Exception as e:
            self.commands_failed += 1
            print(f"Velocity command failed: {e}")
    
    def _send_current_command(self, current):
        """Send current command with error tracking"""
        try:
            if self.motor.set_current(self.motor_id, current):
                self.commands_sent += 1
            else:
                self.commands_failed += 1
        except Exception as e:
            self.commands_failed += 1
            print(f"Current command failed: {e}")
    
    def _send_position_command(self, position):
        """Send position command with error tracking"""
        try:
            if self.motor.set_position(self.motor_id, position):
                self.commands_sent += 1
            else:
                self.commands_failed += 1
        except Exception as e:
            self.commands_failed += 1
            print(f"Position command failed: {e}")
    
    def _switch_mode(self, mode):
        """Switch mode with error tracking"""
        try:
            if self.motor.set_mode(self.motor_id, mode):
                self.mode_switches += 1
            else:
                self.commands_failed += 1
        except Exception as e:
            self.commands_failed += 1
            print(f"Mode switch failed: {e}")
    
    def run_stress_test(self, duration=60):
        """Run comprehensive stress test"""
        print("🚨 STARTING AGGRESSIVE GUI STRESS TEST")
        print("=" * 60)
        print(f"This will simulate chaotic user input for {duration} seconds")
        print("Watch for:")
        print("- Commands getting stuck or ignored")
        print("- Mode switching failures")
        print("- Feedback interruptions")
        print("- System becoming unresponsive")
        print("=" * 60)
        
        if not self.connect_motor():
            return False
        
        self.test_running = True
        start_time = time.time()
        
        # Start chaos threads
        threads = [
            threading.Thread(target=self.random_slider_chaos, daemon=True),
            threading.Thread(target=self.button_masher, daemon=True),
            threading.Thread(target=self.feedback_monitor, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        try:
            # Let chaos run for specified duration
            while time.time() - start_time < duration and self.test_running:
                time.sleep(1)
                
                # Print status every 10 seconds
                if int(time.time() - start_time) % 10 == 0:
                    elapsed = int(time.time() - start_time)
                    success_rate = (self.commands_sent / (self.commands_sent + self.commands_failed)) * 100 if (self.commands_sent + self.commands_failed) > 0 else 0
                    print(f"⏱️ {elapsed}s - Commands: {self.commands_sent} ✅ {self.commands_failed} ❌ ({success_rate:.1f}% success)")
        
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        
        self.test_running = False
        
        # Final stats
        total_commands = self.commands_sent + self.commands_failed
        success_rate = (self.commands_sent / total_commands) * 100 if total_commands > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 STRESS TEST RESULTS")
        print("=" * 60)
        print(f"Duration: {time.time() - start_time:.1f} seconds")
        print(f"Commands sent: {self.commands_sent}")
        print(f"Commands failed: {self.commands_failed}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Mode switches: {self.mode_switches}")
        print(f"Feedback failures: {self.feedback_failures}")
        
        if success_rate < 90:
            print("❌ POOR PERFORMANCE - High command failure rate")
        elif self.commands_failed > total_commands * 0.05:
            print("⚠️ MODERATE ISSUES - Some commands failing")
        else:
            print("✅ GOOD PERFORMANCE - System handled chaos well")
        
        print("\n💡 Issues indicate need for:")
        if self.commands_failed > 10:
            print("- Command queuing system")
            print("- Better error handling")
        if self.mode_switches < 5:
            print("- More reliable mode switching")
        if self.feedback_failures > 20:
            print("- Feedback system improvements")
        
        self.motor.disconnect()
        return True

def main():
    print("🔥 DDSM115 GUI Stress Tester")
    print("This simulates aggressive user behavior to find breaking points")
    
    duration = int(input("Test duration in seconds (default 30): ") or "30")
    
    tester = GUIStressTest()
    tester.run_stress_test(duration)

if __name__ == "__main__":
    main()