#!/usr/bin/env python3
"""
Test script to verify Tkinter callback tracking and cleanup
"""
import tkinter as tk
import signal
import sys
import time

class CallbackTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Callback Test")
        self.root.geometry("300x200")
        
        # Track all scheduled callbacks for cleanup
        self._scheduled_callbacks = set()
        self._shutdown_in_progress = False
        
        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._handle_sigint)
        
        # Start some test callbacks
        self.start_test_callbacks()
        
    def schedule_callback(self, delay_ms, callback):
        """Safely schedule a callback and track it for cleanup"""
        if self._shutdown_in_progress:
            return None
        
        try:
            # Wrap the callback to auto-cleanup when executed
            def wrapped_callback():
                try:
                    callback()
                finally:
                    # Remove from tracking when callback completes
                    self._scheduled_callbacks.discard(callback_id)
            
            callback_id = self.root.after(delay_ms, wrapped_callback)
            self._scheduled_callbacks.add(callback_id)
            print(f"Scheduled callback {callback_id}, total: {len(self._scheduled_callbacks)}")
            return callback_id
        except Exception as e:
            print(f"Error scheduling callback: {e}")
            return None
    
    def cancel_all_callbacks(self):
        """Cancel all tracked callbacks"""
        print(f"Canceling {len(self._scheduled_callbacks)} callbacks")
        for callback_id in list(self._scheduled_callbacks):
            try:
                self.root.after_cancel(callback_id)
            except Exception as e:
                print(f"Error canceling callback {callback_id}: {e}")
        self._scheduled_callbacks.clear()
        print("All callbacks canceled")
    
    def start_test_callbacks(self):
        """Start some recurring test callbacks"""
        def test_callback_1():
            if not self._shutdown_in_progress:
                print(f"Test callback 1 - Active callbacks: {len(self._scheduled_callbacks)}")
                self.schedule_callback(1000, test_callback_1)
        
        def test_callback_2():
            if not self._shutdown_in_progress:
                print(f"Test callback 2 - Active callbacks: {len(self._scheduled_callbacks)}")
                self.schedule_callback(1500, test_callback_2)
        
        def test_callback_3():
            if not self._shutdown_in_progress:
                print(f"Test callback 3 - Active callbacks: {len(self._scheduled_callbacks)}")
                self.schedule_callback(2000, test_callback_3)
        
        # Start the callbacks
        self.schedule_callback(100, test_callback_1)
        self.schedule_callback(200, test_callback_2)
        self.schedule_callback(300, test_callback_3)
    
    def _handle_sigint(self, signum, frame):
        """Handle Ctrl+C"""
        print("\n⚡ Ctrl+C detected - Starting cleanup...")
        self._shutdown_in_progress = True
        
        # Cancel all callbacks first
        self.cancel_all_callbacks()
        
        # Then exit
        print("Exiting...")
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        sys.exit(0)
    
    def run(self):
        print("Starting callback test. Press Ctrl+C to test cleanup.")
        print("You should see no 'invalid command name' errors on shutdown.")
        self.root.mainloop()

if __name__ == "__main__":
    test = CallbackTest()
    test.run()