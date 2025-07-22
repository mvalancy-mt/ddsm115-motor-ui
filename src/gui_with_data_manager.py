"""
Example integration of the GUI with the new Motor Data Manager
This shows how to refactor the existing GUI to use the centralized data system
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from collections import deque

# Import the new data manager components
from motor_data_manager import (
    MotorDataManager, 
    GraphDataListener, 
    UIStatusListener,
    DataEventType
)

# Import matplotlib for graphing
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib import animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ModernMotorGUI:
    """Example GUI using the new Motor Data Manager architecture"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DDSM115 Motor Control - Data Manager Architecture")
        self.root.geometry("1000x700")
        
        # Initialize data manager and listeners
        self.data_manager = MotorDataManager()
        self.graph_listener = GraphDataListener()
        self.ui_listener = UIStatusListener()
        
        # UI state
        self.selected_motor_id = tk.IntVar(value=1)
        self.is_connected = False
        
        # Setup GUI
        self.setup_ui()
        self.setup_graph()
        
        # Register listeners with data manager
        self.data_manager.register_listener(self.graph_listener)
        self.data_manager.register_listener(self.ui_listener)
        
        # Start UI update loop
        self.start_ui_updates()
    
    def setup_ui(self):
        """Setup the main UI components"""
        
        # Connection panel
        conn_frame = ttk.LabelFrame(self.root, text="Connection")
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side="left", padx=5, pady=5)
        
        self.connection_status = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.connection_status.pack(side="left", padx=10)
        
        # Motor selection panel
        motor_frame = ttk.LabelFrame(self.root, text="Motor Selection")
        motor_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(motor_frame, text="Motor ID:").pack(side="left", padx=5)
        
        motor_spinbox = ttk.Spinbox(motor_frame, from_=1, to=10, 
                                   textvariable=self.selected_motor_id, width=5)
        motor_spinbox.pack(side="left", padx=5)
        motor_spinbox.bind('<KeyRelease>', self.on_motor_selection_changed)
        motor_spinbox.bind('<<Increment>>', self.on_motor_selection_changed)
        motor_spinbox.bind('<<Decrement>>', self.on_motor_selection_changed)
        
        # Connected motors display
        self.connected_motors_label = ttk.Label(motor_frame, text="Connected: None")
        self.connected_motors_label.pack(side="left", padx=20)
        
        # Status display panel
        status_frame = ttk.LabelFrame(self.root, text="Motor Status")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # Create status labels
        self.status_labels = {}
        status_items = [
            ("Velocity", "velocity", "RPM"),
            ("Position", "position", "°"), 
            ("Torque", "torque", "A"),
            ("Temperature", "temperature", "°C")
        ]
        
        for i, (name, key, unit) in enumerate(status_items):
            label = ttk.Label(status_frame, text=f"{name}: -- {unit}")
            label.grid(row=0, column=i, padx=10, pady=5)
            self.status_labels[key] = label
        
        # Control panel
        control_frame = ttk.LabelFrame(self.root, text="Motor Control")
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Velocity control
        ttk.Label(control_frame, text="Velocity:").grid(row=0, column=0, padx=5)
        self.velocity_var = tk.DoubleVar()
        ttk.Scale(control_frame, from_=-100, to=100, variable=self.velocity_var, 
                 orient="horizontal", length=200).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Set Velocity", 
                  command=self.set_velocity).grid(row=0, column=2, padx=5)
        
        # Position control  
        ttk.Label(control_frame, text="Position:").grid(row=1, column=0, padx=5)
        self.position_var = tk.DoubleVar()
        ttk.Scale(control_frame, from_=0, to=360, variable=self.position_var,
                 orient="horizontal", length=200).grid(row=1, column=1, padx=5)
        ttk.Button(control_frame, text="Set Position",
                  command=self.set_position).grid(row=1, column=2, padx=5)
        
        # Emergency controls
        emergency_frame = ttk.Frame(control_frame)
        emergency_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(emergency_frame, text="STOP", command=self.emergency_stop,
                  style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(emergency_frame, text="Enable", command=self.enable_motor).pack(side="left", padx=5)
        ttk.Button(emergency_frame, text="Disable", command=self.disable_motor).pack(side="left", padx=5)
        
        # Log panel
        log_frame = ttk.LabelFrame(self.root, text="Event Log")
        log_frame.pack(fill="x", padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=6, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
    
    def setup_graph(self):
        """Setup the matplotlib graph"""
        if not MATPLOTLIB_AVAILABLE:
            graph_frame = ttk.LabelFrame(self.root, text="Graph (Matplotlib not available)")
            graph_frame.pack(fill="both", expand=True, padx=10, pady=5)
            ttk.Label(graph_frame, text="Install matplotlib to see real-time graphs").pack(pady=20)
            return
        
        # Graph panel
        graph_frame = ttk.LabelFrame(self.root, text="Real-time Graph")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 4), dpi=80)
        
        # Velocity subplot
        self.ax1 = self.fig.add_subplot(131)
        self.ax1.set_title("Velocity")
        self.ax1.set_ylabel("RPM")
        self.ax1.grid(True, alpha=0.3)
        
        # Position subplot
        self.ax2 = self.fig.add_subplot(132)
        self.ax2.set_title("Position")
        self.ax2.set_ylabel("Degrees")
        self.ax2.grid(True, alpha=0.3)
        
        # Torque subplot
        self.ax3 = self.fig.add_subplot(133)
        self.ax3.set_title("Torque")
        self.ax3.set_ylabel("Amps")
        self.ax3.grid(True, alpha=0.3)
        
        # Initialize empty lines
        self.velocity_line, = self.ax1.plot([], [], 'b-', linewidth=2)
        self.position_line, = self.ax2.plot([], [], 'r-', linewidth=2)
        self.torque_line, = self.ax3.plot([], [], 'g-', linewidth=2)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Start animation
        self.ani = animation.FuncAnimation(self.fig, self.update_graph, interval=200, blit=False)
    
    def update_graph(self, frame):
        """Update graph with latest data from graph listener"""
        if not MATPLOTLIB_AVAILABLE:
            return []
        
        # Process any pending events
        self.graph_listener.process_events()
        
        # Get data for selected motor
        motor_id = self.selected_motor_id.get()
        plot_data = self.graph_listener.get_plot_data(motor_id)
        
        if not plot_data or not plot_data['time']:
            # Show "No data" message
            for ax in [self.ax1, self.ax2, self.ax3]:
                ax.clear()
                ax.text(0.5, 0.5, f'No data from Motor {motor_id}', 
                       transform=ax.transAxes, ha='center', va='center',
                       fontsize=12, color='red')
            return []
        
        # Convert timestamps to relative time
        times = list(plot_data['time'])
        start_time = times[0] if times else time.time()
        rel_times = [(t - start_time) for t in times]
        
        # Update velocity plot
        self.ax1.clear()
        self.ax1.plot(rel_times, list(plot_data['velocity']), 'b-', linewidth=2)
        self.ax1.set_title(f"Motor {motor_id} Velocity")
        self.ax1.set_ylabel("RPM")
        self.ax1.grid(True, alpha=0.3)
        
        # Update position plot
        self.ax2.clear()
        self.ax2.plot(rel_times, list(plot_data['position']), 'r-', linewidth=2)
        self.ax2.set_title(f"Motor {motor_id} Position")
        self.ax2.set_ylabel("Degrees")
        self.ax2.grid(True, alpha=0.3)
        
        # Update torque plot
        self.ax3.clear()
        self.ax3.plot(rel_times, list(plot_data['torque']), 'g-', linewidth=2)
        self.ax3.set_title(f"Motor {motor_id} Torque")
        self.ax3.set_ylabel("Amps")
        self.ax3.grid(True, alpha=0.3)
        
        return []
    
    def start_ui_updates(self):
        """Start the UI update loop"""
        self.update_ui()
    
    def update_ui(self):
        """Update UI elements with latest data"""
        try:
            # Process UI listener events
            self.ui_listener.process_events()
            
            # Update connected motors display
            connected = self.data_manager.get_connected_motors()
            if connected:
                self.connected_motors_label.config(text=f"Connected: {', '.join(map(str, connected))}")
            else:
                self.connected_motors_label.config(text="Connected: None")
            
            # Update status for selected motor
            motor_id = self.selected_motor_id.get()
            status = self.ui_listener.get_latest_status(motor_id)
            
            if status and status.get('connected', False):
                # Update status labels
                self.status_labels['velocity'].config(
                    text=f"Velocity: {status.get('velocity', 0):.1f} RPM")
                self.status_labels['position'].config(
                    text=f"Position: {status.get('position', 0):.1f} °")
                self.status_labels['torque'].config(
                    text=f"Torque: {status.get('torque', 0):.2f} A")
                self.status_labels['temperature'].config(
                    text=f"Temperature: {status.get('temperature', 0):.1f} °C")
            else:
                # Show no data
                for key in self.status_labels:
                    unit = {"velocity": "RPM", "position": "°", "torque": "A", "temperature": "°C"}[key]
                    self.status_labels[key].config(text=f"{key.title()}: -- {unit}")
            
            # Schedule next update
            self.root.after(100, self.update_ui)
            
        except Exception as e:
            self.log(f"UI update error: {e}")
            self.root.after(1000, self.update_ui)  # Retry after longer delay
    
    def toggle_connection(self):
        """Toggle connection to motor controller"""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connect to motor controller"""
        self.log("🔌 Connecting to motor controller...")
        
        if self.data_manager.connect():
            self.is_connected = True
            self.connect_btn.config(text="Disconnect")
            self.connection_status.config(text="Connected", foreground="green")
            self.log("✅ Connected successfully")
        else:
            self.log("❌ Connection failed")
    
    def disconnect(self):
        """Disconnect from motor controller"""
        self.log("🔌 Disconnecting...")
        self.data_manager.disconnect()
        self.is_connected = False
        self.connect_btn.config(text="Connect")
        self.connection_status.config(text="Disconnected", foreground="red")
        self.log("⏹️ Disconnected")
    
    def on_motor_selection_changed(self, event=None):
        """Handle motor selection change"""
        motor_id = self.selected_motor_id.get()
        self.log(f"🔄 Selected Motor ID: {motor_id}")
        
        # Clear graph data for new motor selection
        if hasattr(self, 'graph_listener'):
            # Could optionally clear data or keep historical data
            pass
    
    def set_velocity(self):
        """Set motor velocity"""
        motor_id = self.selected_motor_id.get()
        velocity = self.velocity_var.get()
        
        if self.data_manager.set_velocity(motor_id, velocity):
            self.log(f"📏 Set Motor {motor_id} velocity to {velocity:.1f} RPM")
        else:
            self.log(f"❌ Failed to set velocity for Motor {motor_id}")
    
    def set_position(self):
        """Set motor position"""
        motor_id = self.selected_motor_id.get()
        position = self.position_var.get()
        
        if self.data_manager.set_position(motor_id, position):
            self.log(f"📍 Set Motor {motor_id} position to {position:.1f}°")
        else:
            self.log(f"❌ Failed to set position for Motor {motor_id}")
    
    def emergency_stop(self):
        """Emergency stop motor"""
        motor_id = self.selected_motor_id.get()
        
        if self.data_manager.stop_motor(motor_id):
            self.log(f"🛑 EMERGENCY STOP Motor {motor_id}")
        else:
            self.log(f"❌ Failed to stop Motor {motor_id}")
    
    def enable_motor(self):
        """Enable motor"""
        motor_id = self.selected_motor_id.get()
        
        if self.data_manager.enable_motor(motor_id):
            self.log(f"🔌 Enabled Motor {motor_id}")
        else:
            self.log(f"❌ Failed to enable Motor {motor_id}")
    
    def disable_motor(self):
        """Disable motor"""
        motor_id = self.selected_motor_id.get()
        
        if self.data_manager.disable_motor(motor_id):
            self.log(f"⏸️ Disabled Motor {motor_id}")
        else:
            self.log(f"❌ Failed to disable Motor {motor_id}")
    
    def log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        print(log_entry.strip())  # Also print to console
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_connected:
            self.disconnect()
        self.root.quit()


def main():
    """Main entry point"""
    print("🚀 Modern Motor GUI with Data Manager")
    print("=" * 50)
    
    root = tk.Tk()
    app = ModernMotorGUI(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()