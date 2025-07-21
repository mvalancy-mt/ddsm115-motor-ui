#!/usr/bin/env python3
"""
Interactive GUI testing script to simulate user interactions and identify issues
"""

import time
import threading
import tkinter as tk
from ddsm115_gui import SimpleDDSM115GUI

class GUITester:
    def __init__(self):
        self.gui = None
        self.test_running = False
        self.issues_found = []
        
    def start_gui(self):
        """Start the GUI in a separate thread"""
        def run_gui():
            self.gui = SimpleDDSM115GUI()
            self.gui.root.mainloop()
        
        gui_thread = threading.Thread(target=run_gui, daemon=True)
        gui_thread.start()
        
        # Wait for GUI to initialize
        time.sleep(2)
        return self.gui is not None

    def simulate_slider_interaction(self, slider_name, target_value):
        """Simulate user dragging and releasing a slider"""
        if not self.gui:
            return False
            
        try:
            print(f"🔧 Testing {slider_name} slider -> {target_value}")
            
            # Find the slider widget
            slider_var = None
            if slider_name == "velocity":
                slider_var = self.gui.velocity_var
            elif slider_name == "position":
                slider_var = self.gui.position_var
            elif slider_name == "current":
                slider_var = self.gui.current_var
            
            if not slider_var:
                self.issues_found.append(f"❌ Could not find {slider_name} slider variable")
                return False
            
            # Record initial state
            initial_value = slider_var.get()
            initial_time = time.time()
            
            # Set the slider value (simulates user moving slider)
            print(f"   Setting {slider_name} from {initial_value} to {target_value}")
            slider_var.set(target_value)
            
            # Simulate button press event
            if hasattr(self.gui, '_on_slider_press'):
                self.gui._on_slider_press(slider_name)
            
            # Small delay to simulate user dragging time
            time.sleep(0.1)
            
            # Simulate button release event (this should trigger the command)
            release_method = getattr(self.gui, f'_on_{slider_name}_release', None)
            if release_method:
                print(f"   Triggering {slider_name} release handler...")
                release_method()
            else:
                self.issues_found.append(f"❌ No release handler found for {slider_name}")
                return False
            
            # Monitor response time and behavior
            response_time = time.time() - initial_time
            print(f"   Response time: {response_time:.3f}s")
            
            if response_time > 1.0:
                self.issues_found.append(f"⚠️ Slow response for {slider_name}: {response_time:.3f}s")
            
            # Check if mode switched correctly
            if hasattr(self.gui, 'control_mode_var'):
                expected_mode = slider_name.capitalize()
                actual_mode = self.gui.control_mode_var.get()
                if actual_mode != expected_mode:
                    self.issues_found.append(f"❌ Mode didn't switch: expected {expected_mode}, got {actual_mode}")
                else:
                    print(f"   ✅ Mode correctly switched to {actual_mode}")
            
            return True
            
        except Exception as e:
            self.issues_found.append(f"❌ Error testing {slider_name}: {e}")
            return False

    def monitor_graph_updates(self, duration=10):
        """Monitor if the graph is updating properly"""
        if not self.gui:
            return False
            
        print(f"📊 Monitoring graph updates for {duration}s...")
        
        # Get initial plot data length
        initial_data_count = len(self.gui.plot_time) if hasattr(self.gui, 'plot_time') else 0
        initial_time = time.time()
        
        time.sleep(duration)
        
        # Check if data was added
        final_data_count = len(self.gui.plot_time) if hasattr(self.gui, 'plot_time') else 0
        
        if final_data_count <= initial_data_count:
            self.issues_found.append("❌ Graph not updating - no new data points added")
            return False
        else:
            print(f"   ✅ Graph updating: {final_data_count - initial_data_count} new data points")
            return True

    def test_connection_sequence(self):
        """Test the connection sequence"""
        if not self.gui:
            return False
            
        print("🔌 Testing connection sequence...")
        
        try:
            # Set port
            if hasattr(self.gui, 'port_var'):
                self.gui.port_var.set('/dev/ttyUSB0')
                print("   Port set to /dev/ttyUSB0")
            
            # Set motor ID
            if hasattr(self.gui, 'motor_id_var'):
                self.gui.motor_id_var.set(4)
                print("   Motor ID set to 4")
            
            # Try connecting
            if hasattr(self.gui, 'connect'):
                print("   Attempting connection...")
                result = self.gui.connect()
                if result:
                    print("   ✅ Connection successful")
                    return True
                else:
                    self.issues_found.append("❌ Connection failed")
                    return False
            else:
                self.issues_found.append("❌ No connect method found")
                return False
                
        except Exception as e:
            self.issues_found.append(f"❌ Connection error: {e}")
            return False

    def run_comprehensive_test(self):
        """Run a comprehensive test suite"""
        print("🚀 Starting Comprehensive GUI Test")
        print("=" * 50)
        
        # Start GUI
        if not self.start_gui():
            print("❌ Failed to start GUI")
            return False
        
        print("✅ GUI started successfully")
        
        # Test connection
        if self.test_connection_sequence():
            print("✅ Connection test passed")
            
            # Wait for initial data
            print("⏳ Waiting for initial data...")
            time.sleep(3)
            
            # Test graph monitoring
            self.monitor_graph_updates(5)
            
            # Test each slider
            test_cases = [
                ("velocity", 50),
                ("velocity", -30),
                ("velocity", 0),
                ("current", 2.0),
                ("current", -1.5),
                ("current", 0),
                ("position", 90.0),
                ("position", 180.0),
                ("position", 0.0)
            ]
            
            for slider_name, value in test_cases:
                success = self.simulate_slider_interaction(slider_name, value)
                if success:
                    print(f"✅ {slider_name} slider test passed")
                    time.sleep(2)  # Wait between tests
                else:
                    print(f"❌ {slider_name} slider test failed")
                
        else:
            print("❌ Connection test failed - skipping slider tests")
        
        # Report results
        print("\n" + "=" * 50)
        print("📋 TEST RESULTS")
        print("=" * 50)
        
        if not self.issues_found:
            print("🎉 All tests passed! No issues found.")
        else:
            print(f"⚠️ Found {len(self.issues_found)} issues:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. {issue}")
        
        print("\n💡 Recommendations:")
        if any("Slow response" in issue for issue in self.issues_found):
            print("- Consider optimizing slider response handlers")
        if any("Graph not updating" in issue for issue in self.issues_found):
            print("- Check monitoring thread and data collection")
        if any("Mode didn't switch" in issue for issue in self.issues_found):
            print("- Verify mode switching logic in slider handlers")
        
        return len(self.issues_found) == 0

def main():
    """Run the interactive GUI test"""
    tester = GUITester()
    
    print("🔧 DDSM115 GUI Interactive Tester")
    print("This tool simulates user interactions to identify GUI issues.")
    print("\nMake sure:")
    print("- Motor is connected to /dev/ttyUSB0")  
    print("- Motor ID is set to 4")
    print("- Motor is powered on")
    
    input("\nPress Enter to start testing...")
    
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 GUI testing completed successfully!")
    else:
        print("\n⚠️ GUI testing found issues that need to be addressed.")

if __name__ == "__main__":
    main()