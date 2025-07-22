#!/usr/bin/env python3
"""
DDSM115 Motor Control GUI - Simplified Clean Interface
Created by Matthew Valancy
Version 1.0.0
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import serial
import serial.tools.list_ports
import threading
import time
import datetime
import struct
from collections import deque
import signal
import sys
import math
import re
import html

# Optional matplotlib imports with fallback
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from ddsm115 import DDSM115, MotorMode
from motor_command_queue import MotorCommandQueue
from about_tabs import create_about_tab

class SimpleDDSM115GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DDSM115 Motor Control v1.0.0")
        self.root.geometry("1071x805")  # Increased width to accommodate dual Y-axis torque scale
        self.root.minsize(950, 700)
        
        # Set dark background
        self.root.configure(bg='#2b2b2b')
        
        # Create custom window controls for touch-friendly operation
        self.create_custom_window_controls()
        
        # Remove standard window decorations for touch-only interface
        # This hides the original OS window buttons since we have custom ones
        self.root.overrideredirect(True)
        
        # Configure touch-friendly styles
        self.setup_touch_styles()
        
        # Motor controller
        self.motor_controller = None
        self.monitoring = False
        
        # Metrics tracking
        self.last_rx_time = 0
        self.last_tx_time = 0
        self.rx_count = 0
        self.tx_count = 0
        self.rx_rate = 0
        self.tx_rate = 0
        self.last_rate_calc = time.time()
        self.status_update_active = True
        
        # Graph data
        self.max_plot_points = 200
        self.plot_time = deque(maxlen=self.max_plot_points)
        self.plot_velocity = deque(maxlen=self.max_plot_points)
        self.plot_torque = deque(maxlen=self.max_plot_points)
        self.plot_position = deque(maxlen=self.max_plot_points)
        
        # Initialize variables
        self.initialize_variables()
        
        # Initialize shutdown control before creating widgets
        self._shutdown_in_progress = False
        
        # Track all scheduled callbacks for proper cleanup
        self._scheduled_callbacks = set()
        
        # Track when sliders are being dragged vs released
        self._slider_dragging = {
            'velocity': False,
            'position': False,
            'current': False
        }
        
        # Create widgets
        self.create_widgets()
        
        # Setup cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._handle_sigint)
        
        # Auto-populate serial ports
        self.refresh_ports()
    
    def schedule_callback(self, delay_ms, callback):
        """Safely schedule a callback and track it for cleanup"""
        if self._shutdown_in_progress:
            return None
        
        try:
            # Schedule the callback first to get the ID
            callback_id = self.root.after(delay_ms, callback)
            self._scheduled_callbacks.add(callback_id)
            return callback_id
        except Exception:
            return None
    
    def cancel_callback(self, callback_id):
        """Cancel a specific callback"""
        if callback_id is None:
            return
        
        try:
            self.root.after_cancel(callback_id)
            self._scheduled_callbacks.discard(callback_id)
        except Exception:
            pass
    
    def cancel_all_callbacks(self):
        """Cancel all tracked callbacks"""
        for callback_id in list(self._scheduled_callbacks):
            try:
                self.root.after_cancel(callback_id)
            except Exception:
                pass
        self._scheduled_callbacks.clear()

    def setup_touch_styles(self):
        """Configure touch-friendly styles for all widgets"""
        style = ttk.Style()
        
        # Set dark theme
        style.theme_use('alt')
        
        # Configure dark colors with subtle selection
        style.configure('.', 
                       background='#2b2b2b',
                       foreground='#e0e0e0',
                       fieldbackground='#3c3c3c',
                       selectbackground='#4a4a4a',  # Slightly lighter gray instead of bright blue
                       selectforeground='#ffffff',
                       borderwidth=0,
                       relief='flat')
        
        # Configure larger buttons with dark theme
        style.configure('Touch.TButton', 
                       padding=(15, 10),
                       background='#4a4a4a',
                       foreground='#e0e0e0',
                       focuscolor='#4a9eff',
                       borderwidth=0,
                       relief='flat')
        style.map('Touch.TButton',
                 background=[('active', '#5a5a5a'), ('pressed', '#3a3a3a')])
        
        style.configure('Action.TButton', 
                       padding=(20, 15), 
                       font=('Arial', 11, 'bold'),
                       background='#4a7c4a',
                       foreground='#ffffff',
                       borderwidth=0,
                       relief='flat')
        style.map('Action.TButton',
                 background=[('active', '#5a8c5a'), ('pressed', '#3a6c3a')])
        
        # Configure smaller control buttons
        style.configure('Control.TButton', 
                       padding=(10, 5), 
                       font=('Arial', 10),
                       background='#4a4a4a',
                       foreground='#e0e0e0',
                       borderwidth=0,
                       relief='flat')
        
        # Configure larger checkbuttons with dark theme
        style.configure('Touch.TCheckbutton', 
                       font=('Arial', 12, 'bold'),
                       background='#2b2b2b',
                       foreground='#e0e0e0',
                       focuscolor='#4a9eff',
                       indicatorsize=20,
                       indicatorcolor='#3c3c3c',
                       indicatorrelief='flat')
        style.map('Touch.TCheckbutton',
                 background=[('active', '#3c3c3c')],
                 foreground=[('active', '#4a9eff')],
                 indicatorcolor=[('selected', '#4a9eff'), ('active', '#5ab3ff')])
        
        # Configure larger labels with dark theme
        style.configure('Touch.TLabel', 
                       font=('Arial', 11),
                       background='#2b2b2b',
                       foreground='#e0e0e0')
        style.configure('TouchBold.TLabel', 
                       font=('Arial', 11, 'bold'),
                       background='#2b2b2b',
                       foreground='#e0e0e0')
        
        # Configure larger combobox with dark theme
        style.configure('Touch.TCombobox', 
                       arrowsize=20,
                       fieldbackground='#3c3c3c',
                       background='#4a4a4a',
                       foreground='#e0e0e0',
                       borderwidth=0,
                       relief='flat')
        
        # Configure larger spinbox with dark theme
        style.configure('Touch.TSpinbox', 
                       arrowsize=20,
                       fieldbackground='#3c3c3c',
                       background='#4a4a4a',
                       foreground='#e0e0e0',
                       borderwidth=0,
                       relief='flat')
        
        # Configure notebook tabs with dark theme
        style.configure('TNotebook.Tab', 
                       padding=(20, 10), 
                       font=('Arial', 11),
                       background='#3c3c3c',
                       foreground='#e0e0e0',
                       borderwidth=0,
                       relief='flat')
        style.map('TNotebook.Tab',
                 background=[('selected', '#4a9eff')])
        
        # Configure notebook background
        style.configure('TNotebook', 
                       background='#2b2b2b',
                       borderwidth=0,
                       relief='flat')
        
        # Configure frames with dark theme
        style.configure('TFrame', 
                       background='#2b2b2b',
                       borderwidth=0,
                       relief='flat')
        style.configure('TLabelFrame', 
                       background='#2b2b2b',
                       foreground='#e0e0e0',
                       borderwidth=0,
                       relief='flat')
        style.configure('TLabelFrame.Label',
                       background='#2b2b2b',
                       foreground='#4a9eff')
        
        # Configure entry fields with dark theme
        style.configure('TEntry',
                       fieldbackground='#3c3c3c',
                       foreground='#e0e0e0',
                       borderwidth=0,
                       relief='flat')
        
        # Configure touch-friendly scale (slider) with consistent dark theme
        style.configure('Touch.Horizontal.TScale', 
                       sliderthickness=56,  # Double height for better visibility
                       background='#2b2b2b',
                       troughcolor='#3c3c3c',
                       borderwidth=0,
                       lightcolor='#5a5a5a',
                       darkcolor='#5a5a5a')
        
        # Slider styles with high contrast handles
        # The key is: colored trough (track) + contrasting handle
        
        # Velocity slider: Blue trough with bright white handle
        style.configure('VelocitySlider.Horizontal.TScale', 
                       sliderthickness=28,
                       background='#2b2b2b',  # Match parent background
                       troughcolor='#3a5f9f',  # Blue trough/track
                       borderwidth=1,
                       relief='solid',
                       bordercolor='#4a6fb0')
        style.map('VelocitySlider.Horizontal.TScale',
                 background=[('active', '#ffffff'), ('pressed', '#e0e0e0')],  # White handle with hover
                 slidercolor=[('', '#ffffff'), ('active', '#f0f0f0')])  
        
        # Position slider: Red trough with bright white handle
        style.configure('PositionSlider.Horizontal.TScale', 
                       sliderthickness=28,
                       background='#2b2b2b',  # Match parent background
                       troughcolor='#9f3a3a',  # Red trough/track
                       borderwidth=1,
                       relief='solid',
                       bordercolor='#b04a4a')
        style.map('PositionSlider.Horizontal.TScale',
                 background=[('active', '#ffffff'), ('pressed', '#e0e0e0')],  # White handle with hover
                 slidercolor=[('', '#ffffff'), ('active', '#f0f0f0')])  
        
        # Current slider: Green trough with bright white handle
        style.configure('CurrentSlider.Horizontal.TScale', 
                       sliderthickness=28,
                       background='#2b2b2b',  # Match parent background
                       troughcolor='#3a9f6b',  # Green trough/track
                       borderwidth=1,
                       relief='solid',
                       bordercolor='#4ab07c')
        style.map('CurrentSlider.Horizontal.TScale',
                 background=[('active', '#ffffff'), ('pressed', '#e0e0e0')],  # White handle with hover
                 slidercolor=[('', '#ffffff'), ('active', '#f0f0f0')])
        
        # Make the trough thicker for all slider types
        for slider_type in ['Velocity.Horizontal.TScale', 'Position.Horizontal.TScale', 'Current.Horizontal.TScale']:
            style.layout(slider_type,
                [('Horizontal.Scale.trough',
                  {'children': [('Horizontal.Scale.slider', 
                                {'side': 'left', 'sticky': ''})],
                   'sticky': 'ew'})])
            style.configure(slider_type, 
                           troughheight=21,
                           gripcount=10,
                           sliderlength=35)
    
    def initialize_variables(self):
        """Initialize all tkinter variables"""
        self.port_var = tk.StringVar()
        self.motor_id_var = tk.IntVar(value=1)
        self.velocity_var = tk.IntVar(value=0)
        self.position_var = tk.DoubleVar(value=0.0)
        self.current_var = tk.DoubleVar(value=0.0)
        self.control_mode_var = tk.StringVar(value="Velocity")
        self.new_motor_id_var = tk.IntVar(value=1)
        
        # Flag to prevent position commands when updating from feedback
        self._updating_position_from_feedback = False
        
        # Register validation commands
        self.register_validation_commands()
        

    def create_widgets(self):
        """Create simplified 3-tab interface"""
        # Create emergency stop button at bottom FIRST
        self.create_emergency_stop_button()
        
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_connection_tab()
        self.create_control_tab()
        # Create about tab using modular approach
        self.about_tabs = create_about_tab(self.notebook, self)

    def create_connection_tab(self):
        """Create simplified connection tab"""
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text="🔌 Connection")
        
        # Connection Section
        conn_frame = ttk.LabelFrame(self.connection_frame, text="Serial Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        # Port selection row
        port_row = ttk.Frame(conn_frame)
        port_row.pack(fill="x", pady=2)
        
        ttk.Label(port_row, text="Port:", style='Touch.TLabel').pack(side="left", padx=2)
        self.port_combo = ttk.Combobox(port_row, textvariable=self.port_var, width=30, 
                                      style='Touch.TCombobox', font=('Arial', 11))
        self.port_combo.pack(side="left", padx=5)
        
        ttk.Button(port_row, text="Refresh", command=self.refresh_ports, 
                  style='Touch.TButton').pack(side="left", padx=5)
        ttk.Button(port_row, text="Connect", command=self.connect_motor, 
                  style='Touch.TButton').pack(side="left", padx=5)
        ttk.Button(port_row, text="Disconnect", command=self.disconnect_motor, 
                  style='Touch.TButton').pack(side="left", padx=5)
        
        self.connection_status = ttk.Label(port_row, text="Disconnected", foreground="red", width=12)
        self.connection_status.pack(side="left", padx=10)
        
        # Motor ID Section
        motor_frame = ttk.LabelFrame(self.connection_frame, text="Motor Setup", padding=10)
        motor_frame.pack(fill="x", padx=10, pady=5)
        
        # Motor ID row
        id_row = ttk.Frame(motor_frame)
        id_row.pack(fill="x", pady=2)
        
        ttk.Label(id_row, text="Motor ID:", style='Touch.TLabel').pack(side="left", padx=2)
        ttk.Spinbox(id_row, from_=1, to=10, textvariable=self.motor_id_var, width=5, 
                   style='Touch.TSpinbox', font=('Arial', 11)).pack(side="left", padx=5)
        ttk.Button(id_row, text="Auto Detect", command=self.auto_detect_motor, 
                  style='Touch.TButton').pack(side="left", padx=5)
        ttk.Button(id_row, text="Set ID", command=self.set_motor_id, 
                  style='Touch.TButton').pack(side="left", padx=5)
        
        # Quick Actions
        action_frame = ttk.LabelFrame(self.connection_frame, text="Quick Actions", padding=10)
        action_frame.pack(fill="x", padx=10, pady=5)
        
        action_row = ttk.Frame(action_frame)
        action_row.pack(fill="x")
        
        ttk.Button(action_row, text="🚀 START MOTOR", command=self.start_motor, 
                  style='Action.TButton').pack(side="left", padx=5)
        ttk.Button(action_row, text="🛑 EMERGENCY STOP", command=self.emergency_stop,
                  style='Action.TButton').pack(side="left", padx=5)
        ttk.Button(action_row, text="🔍 DIAGNOSE", command=self.diagnose_motor,
                  style='Action.TButton').pack(side="left", padx=5)
        
        # Status Display
        status_frame = ttk.LabelFrame(self.connection_frame, text="Motor Status", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill="x")
        
        ttk.Label(status_grid, text="Velocity:", style='TouchBold.TLabel').grid(row=0, column=0, sticky="w", padx=5)
        self.status_velocity = ttk.Label(status_grid, text="0 RPM", foreground="#66ccff", width=10,
                                       font=('Arial', 12), background='#2b2b2b')
        self.status_velocity.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(status_grid, text="Position:", style='TouchBold.TLabel').grid(row=0, column=2, sticky="w", padx=15)
        self.status_position = ttk.Label(status_grid, text="0.0°", foreground="#cc66ff", width=8,
                                       font=('Arial', 12), background='#2b2b2b')
        self.status_position.grid(row=0, column=3, sticky="w", padx=5)
        
        ttk.Label(status_grid, text="Torque:", style='TouchBold.TLabel').grid(row=0, column=4, sticky="w", padx=15)
        self.status_torque = ttk.Label(status_grid, text="0 A", foreground="#66ffcc", width=8,
                                     font=('Arial', 12), background='#2b2b2b')
        self.status_torque.grid(row=0, column=5, sticky="w", padx=5)
        
        ttk.Label(status_grid, text="Temperature:", style='TouchBold.TLabel').grid(row=0, column=6, sticky="w", padx=15)
        self.status_temperature = ttk.Label(status_grid, text="N/A", foreground="#ffcc66", width=6,
                                          font=('Arial', 12), background='#2b2b2b')
        self.status_temperature.grid(row=0, column=7, sticky="w", padx=5)
        
        # Connection Log
        log_frame = ttk.LabelFrame(self.connection_frame, text="Connection Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.connection_log = scrolledtext.ScrolledText(log_frame, height=10, width=80,
                                                      bg='#3c3c3c', fg='#e0e0e0',
                                                      insertbackground='#e0e0e0',
                                                      selectbackground='#4a9eff')
        self.connection_log.pack(fill="both", expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill="x", pady=5)
        
        ttk.Button(log_controls, text="Clear Log", command=self.clear_log,
                  style='Touch.TButton').pack(side="left", padx=5)

    def create_control_tab(self):
        """Create control tab with motor controls and live graph"""
        self.control_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.control_frame, text="🎮 Control")
        
        # Left panel - Controls
        left_panel = ttk.Frame(self.control_frame)
        left_panel.pack(side="left", fill="y", padx=5, pady=5)
        
        # Control Mode Selection
        mode_frame = ttk.LabelFrame(left_panel, text="Control Mode", padding=10)
        mode_frame.pack(fill="x", pady=5)
        
        mode_row = ttk.Frame(mode_frame)
        mode_row.pack(fill="x")
        
        ttk.Label(mode_row, text="Current Mode:", style='Touch.TLabel').pack(side="left", padx=2)
        self.mode_display = ttk.Label(mode_row, textvariable=self.control_mode_var, 
                                style='Touch.TLabel', font=('Arial', 11, 'bold'),
                                foreground='#4a9eff')
        self.mode_display.pack(side="left", padx=5)
        
        # Info label about auto-switching
        ttk.Label(mode_row, text="(auto-switches when using sliders)", 
                 style='Touch.TLabel', font=('Arial', 9), 
                 foreground='#888888').pack(side="left", padx=5)
        
        # Velocity Control
        vel_frame = ttk.LabelFrame(left_panel, text="Velocity Control", padding=5)
        vel_frame.pack(fill="x", pady=3)
        
        ttk.Label(vel_frame, text="Speed (RPM):", style='Touch.TLabel').pack()
        
        # Slider and entry on same row with colored background
        slider_row = ttk.Frame(vel_frame)
        slider_row.pack(fill="x", pady=5)
        
        # Create colored background for velocity slider (blue)
        vel_bg = tk.Frame(slider_row, bg="#3a5f9f", height=35)
        vel_bg.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        vel_scale = ttk.Scale(vel_bg, from_=-143, to=143, variable=self.velocity_var, 
                            orient="horizontal", length=180,
                            style='VelocitySlider.Horizontal.TScale')
        # Velocity is integer - no decimal rounding needed
        vel_scale.pack(fill="x", padx=5, pady=5)
        
        # Bind mouse events for drag start/end detection
        vel_scale.bind('<Button-1>', lambda e: self._on_slider_press('velocity'))
        vel_scale.bind('<ButtonRelease-1>', lambda e: self._on_velocity_release())
        
        vel_entry = ttk.Entry(slider_row, textvariable=self.velocity_var, width=6,
                            font=('Arial', 12), validate='key',
                            validatecommand=self.vcmd_int)
        vel_entry.pack(side="right", padx=(5, 0))
        
        # No buttons needed - slider handles everything
        
        # Position Control
        pos_frame = ttk.LabelFrame(left_panel, text="Position Control", padding=5)
        pos_frame.pack(fill="x", pady=3)
        
        ttk.Label(pos_frame, text="Position (°):", style='Touch.TLabel').pack()
        
        # Slider and entry on same row with colored background
        pos_slider_row = ttk.Frame(pos_frame)
        pos_slider_row.pack(fill="x", pady=5)
        
        # Create colored background for position slider (red)
        pos_bg = tk.Frame(pos_slider_row, bg="#9f3a3a", height=35)
        pos_bg.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        pos_scale = ttk.Scale(pos_bg, from_=0, to=360, variable=self.position_var, 
                            orient="horizontal", length=180,
                            style='PositionSlider.Horizontal.TScale')
        pos_scale.pack(fill="x", padx=5, pady=5)
        
        # Bind mouse events for drag start/end detection
        pos_scale.bind('<Button-1>', lambda e: self._on_slider_press('position'))
        pos_scale.bind('<ButtonRelease-1>', lambda e: self._on_position_release())
        
        pos_entry = ttk.Entry(pos_slider_row, textvariable=self.position_var, width=6,
                            font=('Arial', 12), validate='key',
                            validatecommand=self.vcmd_decimal)
        pos_entry.pack(side="right", padx=(5, 0))
        
        # No buttons needed - slider handles everything
        
        # Current Control
        curr_frame = ttk.LabelFrame(left_panel, text="Current Control", padding=5)
        curr_frame.pack(fill="x", pady=3)
        
        ttk.Label(curr_frame, text="Current (A):", style='Touch.TLabel').pack()
        
        # Slider and entry on same row with colored background
        curr_slider_row = ttk.Frame(curr_frame)
        curr_slider_row.pack(fill="x", pady=5)
        
        # Create colored background for current slider (green)
        curr_bg = tk.Frame(curr_slider_row, bg="#3a9f6b", height=35)
        curr_bg.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        curr_scale = ttk.Scale(curr_bg, from_=-8, to=8, variable=self.current_var, 
                             orient="horizontal", length=180,
                             style='CurrentSlider.Horizontal.TScale')
        curr_scale.pack(fill="x", padx=5, pady=5)
        
        # Bind mouse events for drag start/end detection
        curr_scale.bind('<Button-1>', lambda e: self._on_slider_press('current'))
        curr_scale.bind('<ButtonRelease-1>', lambda e: self._on_current_release())
        
        curr_entry = ttk.Entry(curr_slider_row, textvariable=self.current_var, width=6,
                             font=('Arial', 12), validate='key',
                             validatecommand=self.vcmd_decimal)
        curr_entry.pack(side="right", padx=(5, 0))
        
        # No buttons needed - slider handles everything
        
        # Right panel - Graph
        right_panel = ttk.Frame(self.control_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        graph_frame = ttk.LabelFrame(right_panel, text="Live Graph", padding=10)
        graph_frame.pack(fill="both", expand=True)
        
        # Graph controls
        graph_controls = ttk.Frame(graph_frame)
        graph_controls.pack(fill="x", pady=5)
        
        self.show_velocity_var = tk.BooleanVar(value=True)
        self.show_position_var = tk.BooleanVar(value=True)
        self.show_torque_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(graph_controls, text="Velocity", variable=self.show_velocity_var,
                       style='Touch.TCheckbutton').pack(side="left", padx=8)
        ttk.Checkbutton(graph_controls, text="Position", variable=self.show_position_var,
                       style='Touch.TCheckbutton').pack(side="left", padx=8)
        ttk.Checkbutton(graph_controls, text="Torque", variable=self.show_torque_var,
                       style='Touch.TCheckbutton').pack(side="left", padx=8)
        ttk.Button(graph_controls, text="Clear", command=self.clear_graph,
                  style='Touch.TButton').pack(side="left", padx=15)
        
        # Setup graph
        if MATPLOTLIB_AVAILABLE:
            print("📊 Setting up matplotlib graph...")
            self.setup_matplotlib_graph(graph_frame)
        else:
            print("⚠️ Matplotlib not available, using text graph")
            self.setup_text_graph(graph_frame)

    def create_custom_window_controls(self):
        """Create custom touch-friendly window controls"""
        # Create a frame at the top of the window for custom controls
        
        # Create scrollable text area for ASCII art with wide scrollbar
        art_text = scrolledtext.ScrolledText(art_frame, font=("Courier", 8), 
                                           bg='#1a1a1a', fg='#00ff00',
                                           insertbackground='#00ff00',
                                           selectbackground='#2a2a2a')
        art_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure wide scrollbar for touch-friendly use
        self.configure_wide_scrollbar(art_text)
        
        # DDSM115 Hub Motor ASCII Art
        ascii_art = """
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                      DDSM115 HUB MOTOR                                           ║
║                                   Servo Motor Controller                                         ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝

                                    ╭─────────────────────╮
                                    │    RS485 Interface │
                                    │   ┌─────────────┐   │
                                    │   │  TX    RX   │   │
                            ┌───────┤   │   A+  A-    │   ├───────┐
                            │       │   │   B+  B-    │   │       │
                    ┌───────┴───┐   │   └─────────────┘   │   ┌───┴───────┐
                    │    CAN    │   ╰─────────────────────╯   │  ENCODER  │
                    │  BUS I/O  │                             │   HALL    │
                    └───────────┘        ╭───────────╮        │  SENSORS  │
                                         │  CONTROL  │        └───────────┘
                 ╔══════════════════════════════════════════════════════════════════════╗
                 ║                      MOTOR HOUSING (HUB)                             ║
                 ║   ╔════════════════════════════════════════════════════════════╗     ║
                 ║   ║                    STATOR WINDINGS                         ║     ║
                 ║   ║                                                            ║     ║
                 ║   ║    Phase A  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐  Phase A             ║     ║
                 ║   ║             │ │ │ │ │ │ │ │ │ │ │ │ │                      ║     ║
                 ║   ║    Phase B  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤  Phase B             ║     ║
                 ║   ║             │ │ │ │ │ │ │ │ │ │ │ │ │                      ║     ║
                 ║   ║    Phase C  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘  Phase C             ║     ║
                 ║   ║                                                            ║     ║
                 ║   ║              ╔═══════════════════════╗                     ║     ║
                 ║   ║              ║     ROTOR MAGNET      ║                     ║     ║
                 ║   ║              ║                       ║                     ║     ║
                 ║   ║              ║   N  S  N  S  N  S    ║                     ║     ║
                 ║   ║              ║   │  │  │  │  │  │    ║                     ║     ║
                 ║   ║              ║   └──┼──┼──┼──┼──┘    ║                     ║     ║
                 ║   ║              ║      │  │  │  │       ║                     ║     ║
                 ║   ║              ║   ┌──┼──┼──┼──┼──┐    ║                     ║     ║
                 ║   ║              ║   │  │  │  │  │  │    ║                     ║     ║
                 ║   ║              ║   S  N  S  N  S  N    ║                     ║     ║
                 ║   ║              ║                       ║                     ║     ║
                 ║   ║              ╚═══════════════════════╝                     ║     ║
                 ║   ║                                                            ║     ║
                 ║   ╚════════════════════════════════════════════════════════════╝     ║
                 ╚══════════════════════════════════════════════════════════════════════╝
                                                    ║                                       
                                                    ║                                       
                                                ┌────▼────┐                                 
                                                │  WHEEL  │                               
                                                │  MOUNT  │                              
                                                └─────────┘                               

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  TECHNICAL SPECIFICATIONS                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ • Voltage Range:      24-48V DC                                                                 │
│ • Max Current:        8A continuous, 16A peak                                                   │
│ • Speed Range:        0-143 RPM (configurable)                                                  │
│ • Position Accuracy:  0.1° resolution                                                           │
│ • Communication:      RS485 (Modbus RTU protocol)                                               │
│ • Control Modes:      Velocity, Position, Current (Torque)                                      │
│ • Encoder Type:       Hall sensor + magnetic encoder                                            │
│ • Operating Temp:     -10°C to +50°C                                                            │
│ • Protection:         IP54 (dust and splash resistant)                                          │
│ • Motor Type:         Brushless DC (BLDC)                                                       │
│ • Pole Pairs:         12 (24 poles)                                                             │
│ • Wheel Diameter:     16" - 24" (application dependent)                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    CONTROL INTERFACE                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│  ┌─ RS485 Communication ─┐     ┌─ This GUI Application ─┐     ┌─ Motor Response  ─┐             │
│  │                       │────▶│                        │────▶│                   │             │
│  │  • Command Packets    │     │  • Real-time Control   │     │  • Position       │             │ 
│  │  • Mode Switching     │     │  • Live Monitoring     │     │  • Velocity       │             │
│  │  • Parameter Setting  │     │  • Emergency Stop      │     │  • Current/Torque │             │
│  │  • Status Requests    │     │  • Data Visualization  │     │  • Temperature    │             │
│  │                       │◀────│                        │◀────│                   │             │
│  └───────────────────────┘     └────────────────────────┘     └───────────────────┘             │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

        Welcome to the DDSM115 Motor Control Interface!
        
        This application provides comprehensive control over DDSM115 hub motors,
        featuring real-time monitoring, intuitive slider controls, and robust
        communication protocols for industrial and robotic applications.
        
"""
        
        art_text.insert(tk.END, ascii_art)
        art_text.config(state='disabled')  # Make read-only
    
    def create_info_tab(self):
        """Create application info tab with rich markdown rendering"""
        info_frame = ttk.Frame(self.about_notebook)
        self.about_notebook.add(info_frame, text="📄 Info")
        
        # Create a frame with scrollbar for the markdown widget
        scroll_frame = ttk.Frame(info_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create wide scrollbar for touch-friendly use (using tk.Scrollbar for width support)
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Configure wide scrollbar
        self.configure_wide_scrollbar_direct(scrollbar)
        
        # Create rich markdown text widget with content
        info_content = """# DDSM115 Motor Control Interface

## Version 1.0.0

**Created by Matthew Valancy**

---

## Overview

A comprehensive interface for controlling DDSM115 servo motors with real-time monitoring and intuitive controls.

### Key Features

- **Real-time Motor Control**: Intuitive sliders for velocity, position, and current control
- **Live Data Visualization**: Dynamic graphs showing motor performance metrics  
- **Automatic Mode Switching**: Seamless transitions between control modes
- **Emergency Safety**: Instant stop functionality for all connected motors
- **Dark Theme Interface**: Optimized for extended use in various lighting conditions
- **Robust Communication**: RS485 protocol with error handling and recovery
- **Multi-motor Support**: Control multiple motors with automatic detection

### Technical Capabilities

- **Control Modes**:
  - Velocity Control: -143 to +143 RPM
  - Position Control: 0° to 360° with 0.1° precision
  - Current Control: -8A to +8A for torque applications

- **Real-time Monitoring**:
  - Motor velocity, position, and torque
  - Temperature monitoring with alerts
  - Communication statistics (TX/RX rates)
  - Connection status and diagnostics

- **Safety Features**:
  - Emergency stop for immediate motor shutdown
  - Automatic velocity ramping for safe mode transitions
  - Connection monitoring with auto-reconnect
  - Error handling and graceful degradation

### Communication Protocol

The application uses RS485 communication with custom packet protocols:
- 10-byte command packets for motor control
- Real-time feedback monitoring at 20Hz
- Automatic motor ID detection and configuration
- Robust error handling and retry mechanisms

### Use Cases

- **Robotics**: Precise control for robotic joints and actuators
- **Industrial Automation**: Conveyor systems and positioning applications
- **Electric Vehicles**: Hub motor control for e-bikes and scooters
- **Research & Development**: Motor characterization and testing
- **Educational**: Learning motor control principles and RS485 communication

### System Requirements

- Python 3.8+ with tkinter, matplotlib, and pyserial
- USB-to-RS485 converter for communication
- DDSM115 motor with proper power supply (24-48V)
- Operating system: Windows, Linux, or macOS

---

This application represents a complete solution for DDSM115 motor control,
combining ease of use with professional-grade functionality.
"""
        
        info_text = self.create_markdown_text_widget(scroll_frame, info_content)
        info_text.pack(side="left", fill="both", expand=True)
        
        # Connect scrollbar to text widget
        scrollbar.config(command=info_text.yview)
        info_text.config(yscrollcommand=scrollbar.set)
    
    def create_operation_guide_tab(self):
        """Create comprehensive operation guide with rich markdown"""
        guide_frame = ttk.Frame(self.about_notebook)
        self.about_notebook.add(guide_frame, text="📖 Operation Guide")
        
        # Create a frame with scrollbar for the markdown widget
        scroll_frame = ttk.Frame(guide_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create wide scrollbar for touch-friendly use (using tk.Scrollbar for width support)
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Configure wide scrollbar
        self.configure_wide_scrollbar_direct(scrollbar)
        
        guide_content = """# DDSM115 Motor Control - Complete Operation Guide

## Table of Contents
1. Getting Started
2. Connection Setup
3. Motor Control
4. Live Monitoring
5. Safety Features
6. Advanced Features

---

## Getting Started

### Initial Setup
1. **Hardware Connection**
   - Connect DDSM115 motor to power supply (24-48V)
   - Connect USB-to-RS485 converter to computer
   - Wire RS485 A+/A- and B+/B- lines to motor
   - Ensure proper grounding and shielding

2. **Software Launch**
   - Run the application using `python3 ddsm115_gui.py`
   - The interface will open with the Connection tab active
   - USB ports will be automatically scanned and populated

### First Connection
1. Select your USB-to-RS485 device from the dropdown
2. Click "Connect" to establish communication
3. Use "Auto Detect" to find your motor ID
4. The status will show "CONNECTED" when successful

---

## Connection Setup

### Port Selection
- **Automatic Detection**: The application scans for USB-to-RS485 devices
- **Manual Selection**: Choose from available serial ports
- **Auto-connect**: Single USB-to-RS485 devices connect automatically

### Motor Detection
- **Auto Detect**: Scans motor IDs 1-10 to find active motors
- **Manual ID**: Set motor ID manually if known
- **Multiple Motors**: Each motor requires a unique ID

### Connection Status
- **Green "CONNECTED"**: Communication established
- **Red "DISCONNECTED"**: No communication
- **Status Bar**: Shows TX/RX rates and connection health

---

## Motor Control

### Control Modes

#### Velocity Control (Blue Slider)
- **Range**: -143 to +143 RPM
- **Use Case**: Continuous rotation applications
- **Auto-switching**: Automatically activates when velocity slider is used
- **Real-time**: Immediate response to slider changes

#### Position Control (Red Slider)  
- **Range**: 0° to 360°
- **Precision**: 0.1° resolution
- **Use Case**: Precise positioning applications
- **Safety**: Automatically ramps down velocity before switching modes

#### Current Control (Green Slider)
- **Range**: -8A to +8A
- **Use Case**: Torque control applications
- **Safety**: Current limiting protects motor from damage

### Slider Operation
- **Touch-friendly**: Large, color-coded sliders for easy operation
- **Release-based**: Commands sent when slider is released (not during drag)
- **Visual Feedback**: Color-coded backgrounds match graph lines
- **Text Entry**: Manual numeric input with validation

### Mode Switching
- **Automatic**: Modes switch automatically when using different sliders
- **Intelligent**: System handles velocity ramping for safe transitions
- **Visual**: Current mode displayed with matching colors
- **Safety**: Emergency stop works in any mode

---

## Live Monitoring

### Real-time Graph
- **Dual Y-axis**: Left axis for velocity/position, right axis for torque
- **Live Updates**: 20Hz refresh rate for smooth visualization
- **Color Coding**: 
  - Blue: Velocity (RPM)
  - Red: Position (degrees)
  - Cyan: Torque (Amps)
- **Auto-scaling**: Axes automatically adjust to data range

### Status Display
- **Velocity**: Current motor speed in RPM
- **Position**: Current motor position in degrees
- **Torque**: Current motor torque in Amps
- **Temperature**: Motor temperature with color alerts
- **Communication**: TX/RX rates and connection status

### Data Logging
- **Continuous**: All data is logged during operation
- **Export**: Data can be exported for analysis
- **History**: Complete session history maintained

---

## Safety Features

### Emergency Stop
- **Big Red Button**: Immediately stops all motor motion
- **All Motors**: Stops motors with IDs 1-10 regardless of current selection
- **Bypass Queue**: Emergency stop bypasses normal command queue
- **Always Active**: Works even during communication errors

### Automatic Safety
- **Velocity Ramping**: Automatic speed reduction before mode changes
- **Temperature Monitoring**: Alerts when motor temperature is high
- **Communication Watchdog**: Detects and recovers from communication errors
- **Error Handling**: Graceful handling of unexpected conditions

### Manual Safety
- **Connection Status**: Always visible connection indicator
- **Mode Display**: Clear indication of current control mode
- **Status Monitoring**: Real-time system health information

---

## Advanced Features

### Diagnostics
- **Motor Test**: Comprehensive motor functionality test
- **Communication Test**: Verifies RS485 communication
- **Movement Test**: Confirms motor responds to commands
- **System Health**: Complete system diagnostic report

### Multi-motor Support
- **Motor Scanning**: Automatically detects all connected motors
- **ID Management**: Easy switching between motor IDs
- **Individual Control**: Each motor controlled independently
- **Status Monitoring**: Monitor multiple motors simultaneously

### Robust Operation
- **Error Recovery**: Automatic recovery from communication errors
- **Long-term Stability**: Designed for weeks of continuous operation
- **Exception Handling**: Comprehensive error handling prevents crashes
- **Graceful Shutdown**: Clean disconnection and resource cleanup

---

## Tips for Best Operation

### Performance Optimization
- Use release-based slider control for smooth operation
- Monitor temperature to prevent overheating
- Ensure stable power supply for consistent performance
- Keep RS485 cables short and properly shielded

### Maintenance
- Regularly check connection status
- Monitor motor temperature during operation
- Verify communication rates are stable
- Test emergency stop functionality periodically

### Troubleshooting Quick Start
1. Check all cable connections
2. Verify power supply voltage and capacity
3. Confirm motor ID settings
4. Test with different USB ports if needed
5. Use diagnostic function to identify issues

This interface is designed for both novice and expert users, providing
simple operation with advanced capabilities when needed.
"""
        
        # Create rich markdown text widget with content
        guide_text = self.create_markdown_text_widget(scroll_frame, guide_content)
        guide_text.pack(side="left", fill="both", expand=True)
        
        # Connect scrollbar to text widget
        scrollbar.config(command=guide_text.yview)
        guide_text.config(yscrollcommand=scrollbar.set)
    
    def create_api_reference_tab(self):
        """Create API reference documentation with rich markdown"""
        api_frame = ttk.Frame(self.about_notebook)
        self.about_notebook.add(api_frame, text="🔧 API Reference")
        
        # Create a frame with scrollbar for the markdown widget
        scroll_frame = ttk.Frame(api_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create wide scrollbar for touch-friendly use (using tk.Scrollbar for width support)
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Configure wide scrollbar
        self.configure_wide_scrollbar_direct(scrollbar)
        
        api_content = """# DDSM115 Motor Control API Reference

## Core Classes

### `MotorCommandQueue`
Main interface for motor control with robust command queuing.

```python
class MotorCommandQueue:
    def __init__(self, port: str = "/dev/ttyUSB0")
    
    # Connection Management
    def connect(self) -> bool
    def disconnect(self) -> None
    def is_connected(self) -> bool
    
    # Motor Control
    def set_velocity(self, motor_id: int, velocity: float, callback: Optional[Callable] = None)
    def set_position(self, motor_id: int, position: float, callback: Optional[Callable] = None)  
    def set_current(self, motor_id: int, current: float, callback: Optional[Callable] = None)
    def set_mode(self, motor_id: int, mode: MotorMode, callback: Optional[Callable] = None)
    
    # Safety
    def stop(self, motor_id: int, callback: Optional[Callable] = None)
    def enable(self, motor_id: int, callback: Optional[Callable] = None)
    def disable(self, motor_id: int, callback: Optional[Callable] = None)
    
    # Monitoring
    def request_feedback(self, motor_id: int, callback: Optional[Callable] = None)
    def get_last_feedback(self, motor_id: int) -> Optional[MotorFeedback]
    def scan_motors(self, start_id: int = 1, end_id: int = 10) -> list
    
    # Statistics
    def get_stats(self) -> dict
```

### Communication Protocol

#### Command Packet Format
All motor commands use 10-byte packets:

```
Byte 0:    Motor ID (1-10)
Byte 1:    Command Type
Bytes 2-8: Command Data (6 bytes)
Byte 9:    Mode/Value
```

#### Command Types
```python
class CommandType(Enum):
    MODE_SWITCH = 0xA0    # Switch control mode
    SET_VELOCITY = 0xA1   # Set velocity command
    SET_POSITION = 0xA2   # Set position command  
    SET_CURRENT = 0xA3    # Set current command
    REQUEST_STATUS = 0xA4 # Request feedback
    ENABLE = 0xA5         # Enable motor
    DISABLE = 0xA6        # Disable motor
```

## Usage Examples

### Basic Motor Control
```python
from motor_command_queue import MotorCommandQueue

# Initialize controller
controller = MotorCommandQueue("/dev/ttyUSB0")

# Connect and find motors
if controller.connect():
    motors = controller.scan_motors()
    if motors:
        motor_id = motors[0]
        
        # Set velocity
        controller.set_velocity(motor_id, 50)  # 50 RPM
        
        # Set position  
        controller.set_position(motor_id, 180)  # 180 degrees
        
        # Set current
        controller.set_current(motor_id, 2.0)   # 2 Amps
        
        # Emergency stop
        controller.stop(motor_id)
        
    controller.disconnect()
```

### Feedback Monitoring
```python
def on_feedback(motor_id, feedback):
    print(f"Motor {motor_id}:")
    print(f"  Velocity: {feedback.velocity} RPM")
    print(f"  Position: {feedback.position}°")
    print(f"  Torque: {feedback.torque} A")

# Setup callback
controller.on_feedback = on_feedback

# Manual feedback request
feedback = controller.request_feedback(motor_id)
if feedback:
    print(f"Current position: {feedback.position}°")
```

### Error Handling
```python
def on_error(error_msg):
    print(f"Motor Error: {error_msg}")

controller.on_error = on_error

# Get statistics
stats = controller.get_stats()
print(f"Commands processed: {stats['commands_processed']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

This API provides both high-level convenience and low-level control
for comprehensive DDSM115 motor management.
"""
        
        # Create rich markdown text widget with content (VS Code dark theme)
        api_text = self.create_markdown_text_widget(scroll_frame, api_content, '#1e1e1e', '#d4d4d4')
        api_text.pack(side="left", fill="both", expand=True)
        
        # Connect scrollbar to text widget
        scrollbar.config(command=api_text.yview)
        api_text.config(yscrollcommand=scrollbar.set)
    
    def create_troubleshooting_tab(self):
        """Create troubleshooting guide with rich markdown"""
        trouble_frame = ttk.Frame(self.about_notebook)
        self.about_notebook.add(trouble_frame, text="🔍 Troubleshooting")
        
        # Create a frame with scrollbar for the markdown widget
        scroll_frame = ttk.Frame(trouble_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create wide scrollbar for touch-friendly use (using tk.Scrollbar for width support)
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Configure wide scrollbar
        self.configure_wide_scrollbar_direct(scrollbar)
        
        trouble_content = """# DDSM115 Troubleshooting Guide

## Quick Diagnostic Checklist

### ❌ Cannot Connect to Motor
**Symptoms**: Connection status shows "DISCONNECTED", no response from motor

**Solutions**:
1. **Check Physical Connections**
   - Verify USB-to-RS485 adapter is plugged in
   - Confirm RS485 wiring: A+ to A+, A- to A-, B+ to B+, B- to B-
   - Ensure motor power supply is connected and switched on
   - Check for loose connections and proper grounding

2. **Verify Port Selection**
   - Try "Refresh Ports" to rescan available ports
   - Select correct USB-to-RS485 device from dropdown
   - Try different USB ports on computer
   - Check if device appears in system device manager

3. **Test Communication Settings**
   - Verify motor is configured for correct baud rate (115200)
   - Check motor ID settings (default usually 1)
   - Try different motor IDs using "Auto Detect"

---

### ⚠️ Motor Detected But Not Responding
**Symptoms**: Motor found during scan but doesn't move when commanded

**Solutions**:
1. **Check Motor State**
   - Use "Diagnose" function to test motor systematically
   - Verify motor is enabled (not in fault state)
   - Check temperature - motor may be in thermal protection

2. **Power Supply Issues**
   - Verify power supply can provide sufficient current (8A+ continuous)
   - Check voltage is within motor specifications (24-48V)
   - Ensure power supply connections are secure

3. **Mechanical Issues**
   - Check for mechanical binding or excessive load
   - Verify motor shaft/wheel can rotate freely
   - Ensure motor mounting is secure

---

### 📊 Graph Not Updating or Freezing
**Symptoms**: Live graph stops updating, shows flat lines

**Solutions**:
1. **Check Communication**
   - Verify TX/RX rates in status bar are non-zero
   - Look for communication error messages
   - Try disconnecting and reconnecting

2. **Software Issues**
   - Close and restart the application
   - Check available system memory
   - Try reducing graph update rate

---

### 🎛️ Sliders Not Working Properly
**Symptoms**: Moving sliders doesn't control motor, or control is erratic

**Solutions**:
1. **Check Mode Switching**
   - Verify current mode display matches expected control
   - Allow time for mode transitions to complete
   - Try manual mode switching before using sliders

2. **Communication Timing**
   - Use release-based control (don't drag continuously)
   - Allow brief pauses between commands
   - Check for command queue overload in status

---

### 🌡️ Temperature Warnings
**Symptoms**: High temperature readings, thermal protection activation

**Solutions**:
1. **Immediate Actions**
   - Reduce motor load or duty cycle
   - Allow motor to cool before continuing operation
   - Check for adequate ventilation around motor

2. **Long-term Solutions**
   - Verify motor is not overloaded for application
   - Check ambient temperature conditions
   - Consider active cooling for high-duty applications

---

### ⚡ Emergency Stop Not Working
**Symptoms**: E-stop button doesn't immediately stop motor

**Solutions**:
1. **Immediate Safety**
   - Remove power from motor immediately
   - Check physical emergency stop switches if installed
   - Verify motor brake engagement (if equipped)

2. **Software Issues**
   - Restart application to clear any software locks
   - Check communication is working before relying on software E-stop
   - Verify emergency stop bypasses normal command queue

---

## When to Contact Support

Contact technical support if:
- Multiple troubleshooting steps don't resolve the issue
- Hardware damage is suspected
- Motor behavior is inconsistent with specifications
- Safety-critical applications require verification

Remember: When in doubt, prioritize safety. Use physical emergency stops
and power disconnection for immediate safety in any uncertain situation.
"""
        
        # Create rich markdown text widget with content
        trouble_text = self.create_markdown_text_widget(scroll_frame, trouble_content)
        trouble_text.pack(side="left", fill="both", expand=True)
        
        # Connect scrollbar to text widget
        scrollbar.config(command=trouble_text.yview)
        trouble_text.config(yscrollcommand=scrollbar.set)
    
    def create_custom_window_controls(self):
        """Create custom touch-friendly window controls"""
        # Create a frame at the top of the window for custom controls
        controls_frame = tk.Frame(self.root, bg='#1a1a1a', height=50)
        controls_frame.pack(fill="x", side="top")
        controls_frame.pack_propagate(False)
        
        # Title label on the left
        title_label = tk.Label(controls_frame, text="DDSM115 Motor Control", 
                              bg='#1a1a1a', fg='#e0e0e0', 
                              font=('Arial', 12, 'bold'))
        title_label.pack(side="left", padx=10, pady=10)
        
        # Window control buttons on the right (4x larger than normal)
        button_frame = tk.Frame(controls_frame, bg='#1a1a1a')
        button_frame.pack(side="right", padx=5, pady=5)
        
        # Minimize button
        minimize_btn = tk.Button(button_frame, text="−", 
                               command=self.minimize_window,
                               bg='#4a4a4a', fg='#e0e0e0', 
                               font=('Arial', 16, 'bold'),
                               width=3, height=1,
                               relief='flat', bd=0,
                               activebackground='#5a5a5a',
                               cursor='hand2')
        minimize_btn.pack(side="left", padx=2)
        
        # Maximize/Restore button
        self.maximize_btn = tk.Button(button_frame, text="□", 
                                    command=self.toggle_maximize,
                                    bg='#4a4a4a', fg='#e0e0e0', 
                                    font=('Arial', 16, 'bold'),
                                    width=3, height=1,
                                    relief='flat', bd=0,
                                    activebackground='#5a5a5a',
                                    cursor='hand2')
        self.maximize_btn.pack(side="left", padx=2)
        
        # Close button
        close_btn = tk.Button(button_frame, text="✕", 
                            command=self.on_closing,
                            bg='#cc4444', fg='#ffffff', 
                            font=('Arial', 16, 'bold'),
                            width=3, height=1,
                            relief='flat', bd=0,
                            activebackground='#dd5555',
                            cursor='hand2')
        close_btn.pack(side="left", padx=2)
        
        # Track window state
        self.is_maximized = False
        self.normal_geometry = "1071x805"
        
        # Make the title area draggable for window movement
        self.make_draggable(controls_frame)
        self.make_draggable(title_label)
    
    def minimize_window(self):
        """Minimize the window"""
        try:
            self.root.iconify()
        except Exception as e:
            print(f"Error minimizing window: {e}")
    
    def toggle_maximize(self):
        """Toggle between fullscreen and normal resizable window state"""
        try:
            if self.is_maximized:
                # Restore to normal resizable state
                self.root.overrideredirect(True)  # Re-enable custom window controls
                self.root.geometry(self.normal_geometry)
                self.root.resizable(True, True)  # Make window resizable
                self.maximize_btn.config(text="□")
                self.is_maximized = False
                print(f"Restored to normal size: {self.normal_geometry}")
            else:
                # Store current geometry before maximizing
                self.normal_geometry = self.root.geometry()
                
                # Get full screen dimensions
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Remove window decorations and go fullscreen
                self.root.overrideredirect(True)
                self.root.geometry(f"{screen_width}x{screen_height}+0+0")
                self.root.resizable(False, False)  # Disable resizing in fullscreen
                
                self.maximize_btn.config(text="❐")
                self.is_maximized = True
                print(f"Maximized to fullscreen: {screen_width}x{screen_height}")
                
        except Exception as e:
            print(f"Error toggling maximize: {e}")
            # Fallback - try basic geometry change
            try:
                if not self.is_maximized:
                    self.normal_geometry = self.root.geometry()
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    self.root.geometry(f"{screen_width}x{screen_height}+0+0")
                    self.maximize_btn.config(text="❐")
                    self.is_maximized = True
                else:
                    self.root.geometry(self.normal_geometry)
                    self.root.resizable(True, True)
                    self.maximize_btn.config(text="□")
                    self.is_maximized = False
            except Exception as e2:
                print(f"Fallback maximize error: {e2}")
    
    def make_draggable(self, widget):
        """Make a widget draggable for window movement"""
        def start_drag(event):
            widget.start_x = event.x
            widget.start_y = event.y
        
        def on_drag(event):
            try:
                x = self.root.winfo_x() + (event.x - widget.start_x)
                y = self.root.winfo_y() + (event.y - widget.start_y)
                self.root.geometry(f"+{x}+{y}")
            except Exception:
                pass  # Ignore drag errors
        
        widget.bind("<Button-1>", start_drag)
        widget.bind("<B1-Motion>", on_drag)
    
    def configure_wide_scrollbar(self, text_widget):
        """Configure wide, touch-friendly scrollbars for text widgets"""
        try:
            # Calculate scrollbar width as 5-10% of window width
            window_width = self.root.winfo_width() if self.root.winfo_width() > 1 else 1071
            scrollbar_width = max(50, int(window_width * 0.07))  # 7% of window width, minimum 50px
            
            # Get the scrollbar from the ScrolledText widget
            vbar = text_widget.vbar
            
            # Configure the scrollbar to be wider and more touch-friendly
            vbar.config(
                width=scrollbar_width,
                borderwidth=2,
                relief='raised',
                bg='#4a4a4a',
                troughcolor='#2b2b2b',
                activebackground='#6a6a6a',
                highlightbackground='#4a4a4a',
                highlightcolor='#6a6a6a'
            )
            
            # Style the scrollbar arrows and thumb for better visibility
            try:
                # Try to configure scrollbar colors (may not work on all systems)
                vbar.config(
                    elementborderwidth=2,
                    arrowcolor='#e0e0e0',
                    activerelief='raised'
                )
            except Exception:
                pass  # Ignore if these options aren't supported
            
        except Exception as e:
            print(f"Warning: Could not configure wide scrollbar: {e}")
            # Continue without wide scrollbars if configuration fails
    
    def configure_wide_scrollbar_direct(self, scrollbar):
        """Configure a scrollbar directly to be wide and touch-friendly"""
        try:
            # Calculate scrollbar width as 7% of window width
            window_width = self.root.winfo_width() if self.root.winfo_width() > 1 else 1071
            scrollbar_width = max(50, int(window_width * 0.07))  # 7% of window width, minimum 50px
            
            # Configure the scrollbar to be wider and more touch-friendly
            scrollbar.config(
                width=scrollbar_width,
                borderwidth=2,
                relief='raised',
                bg='#4a4a4a',
                troughcolor='#2b2b2b',
                activebackground='#6a6a6a',
                highlightbackground='#4a4a4a',
                highlightcolor='#6a6a6a'
            )
            
        except Exception as e:
            print(f"Warning: Could not configure wide scrollbar directly: {e}")
    
    def create_markdown_text_widget(self, parent, content, bg_color='#2b2b2b', fg_color='#e0e0e0'):
        """Create a rich text widget with markdown-style formatting"""
        text_widget = tk.Text(parent, 
                             font=("Arial", 10), 
                             bg=bg_color, 
                             fg=fg_color,
                             insertbackground=fg_color,
                             selectbackground='#4a9eff',
                             wrap='word',
                             state='disabled',
                             padx=20,
                             pady=15)
        
        # Configure text styles for markdown rendering
        text_widget.tag_configure('h1', font=('Arial', 18, 'bold'), foreground='#ffffff', spacing1=10, spacing3=10)
        text_widget.tag_configure('h2', font=('Arial', 16, 'bold'), foreground='#e0e0e0', spacing1=8, spacing3=8)
        text_widget.tag_configure('h3', font=('Arial', 14, 'bold'), foreground='#d0d0d0', spacing1=6, spacing3=6)
        text_widget.tag_configure('bold', font=('Arial', 10, 'bold'), foreground='#ffffff')
        text_widget.tag_configure('italic', font=('Arial', 10, 'italic'), foreground='#c0c0c0')
        text_widget.tag_configure('code', font=('Courier', 9), background='#1a1a1a', foreground='#00ff00', relief='solid', borderwidth=1)
        text_widget.tag_configure('code_block', font=('Courier', 9), background='#1a1a1a', foreground='#d4d4d4', relief='solid', borderwidth=1, lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5)
        text_widget.tag_configure('bullet', font=('Arial', 10), lmargin1=40, lmargin2=60)
        text_widget.tag_configure('numbered', font=('Arial', 10), lmargin1=40, lmargin2=60)
        text_widget.tag_configure('blockquote', font=('Arial', 10, 'italic'), foreground='#a0a0a0', lmargin1=40, lmargin2=40, relief='solid', borderwidth=1, background='#3a3a3a')
        text_widget.tag_configure('link', font=('Arial', 10, 'underline'), foreground='#4a9eff')
        text_widget.tag_configure('separator', relief='solid', borderwidth=1, background='#555555')
        
        # Render markdown content
        self.render_markdown(text_widget, content)
        
        return text_widget
    
    def render_markdown(self, text_widget, content):
        """Render markdown content in a text widget with styling"""
        text_widget.config(state='normal')
        text_widget.delete(1.0, 'end')
        
        lines = content.split('\n')
        in_code_block = False
        code_block_content = []
        list_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Handle code blocks
            if stripped.startswith('```'):
                if in_code_block:
                    # End code block
                    code_text = '\n'.join(code_block_content)
                    text_widget.insert('end', code_text + '\n', 'code_block')
                    code_block_content = []
                    in_code_block = False
                else:
                    # Start code block
                    in_code_block = True
                continue
            
            if in_code_block:
                code_block_content.append(line)
                continue
            
            # Handle headers
            if stripped.startswith('# '):
                text_widget.insert('end', stripped[2:] + '\n', 'h1')
            elif stripped.startswith('## '):
                text_widget.insert('end', stripped[3:] + '\n', 'h2')
            elif stripped.startswith('### '):
                text_widget.insert('end', stripped[4:] + '\n', 'h3')
            
            # Handle horizontal rules
            elif stripped == '---':
                text_widget.insert('end', '─' * 80 + '\n', 'separator')
            
            # Handle bullet lists
            elif stripped.startswith('- ') or stripped.startswith('• '):
                bullet_text = '• ' + stripped[2:]
                text_widget.insert('end', bullet_text + '\n', 'bullet')
            
            # Handle numbered lists
            elif re.match(r'^\d+\. ', stripped):
                text_widget.insert('end', stripped + '\n', 'numbered')
            
            # Handle blockquotes
            elif stripped.startswith('> '):
                text_widget.insert('end', stripped[2:] + '\n', 'blockquote')
            
            # Handle regular paragraphs with inline formatting
            elif stripped:
                self.render_inline_formatting(text_widget, stripped + '\n')
            
            # Handle empty lines
            else:
                text_widget.insert('end', '\n')
        
        text_widget.config(state='disabled')
    
    def render_inline_formatting(self, text_widget, text):
        """Render inline markdown formatting like bold, italic, code"""
        pos = 0
        
        # Process text character by character to handle inline formatting
        while pos < len(text):
            # Bold text **text**
            bold_match = re.search(r'\*\*(.*?)\*\*', text[pos:])
            # Italic text *text*
            italic_match = re.search(r'\*(.*?)\*', text[pos:])
            # Inline code `code`
            code_match = re.search(r'`(.*?)`', text[pos:])
            
            # Find the earliest match
            matches = []
            if bold_match:
                matches.append((bold_match.start() + pos, bold_match.end() + pos, bold_match.group(1), 'bold'))
            if italic_match and (not bold_match or italic_match.start() < bold_match.start()):
                matches.append((italic_match.start() + pos, italic_match.end() + pos, italic_match.group(1), 'italic'))
            if code_match and (not bold_match or code_match.start() < bold_match.start()) and (not italic_match or code_match.start() < italic_match.start()):
                matches.append((code_match.start() + pos, code_match.end() + pos, code_match.group(1), 'code'))
            
            if matches:
                # Sort by start position
                matches.sort(key=lambda x: x[0])
                start, end, content, style = matches[0]
                
                # Insert text before the match
                if start > pos:
                    text_widget.insert('end', text[pos:start])
                
                # Insert the formatted text
                text_widget.insert('end', content, style)
                
                pos = end
            else:
                # No more matches, insert the rest
                text_widget.insert('end', text[pos:])
                break
    
    def create_emergency_stop_button(self):
        """Create emergency stop button and status bar at bottom of window"""
        # Create container for both E-stop and status bar
        bottom_frame = tk.Frame(self.root, bg='#2b2b2b')
        bottom_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        
        # Create status bar (20% of E-stop height)
        self.create_status_bar(bottom_frame)
        
        # Create the emergency stop button
        self.estop_button = tk.Button(
            bottom_frame,
            text="🛑 EMERGENCY STOP",
            command=self.emergency_stop_all,
            bg="#FF0000",
            fg="white",
            font=("Arial", 18, "bold"),
            height=2,
            pady=10,
            state="disabled",  # Start disabled
            activebackground="#CC0000",
            activeforeground="white",
            relief="raised",
            bd=5,
            cursor="hand2"
        )
        self.estop_button.pack(fill="x", expand=True, pady=(5, 0))
    
    def create_status_bar(self, parent):
        """Create status bar with connection metrics"""
        status_frame = tk.Frame(parent, bg="#2b2b2b", height=30)
        status_frame.pack(fill="x", pady=(0, 5))
        status_frame.pack_propagate(False)
        
        # Connection status
        self.status_conn_label = tk.Label(status_frame, text="⚡ DISCONNECTED", 
                                        bg="#2b2b2b", fg="#ff6666", 
                                        font=("Arial", 10, "bold"),
                                        width=15, anchor="w")
        self.status_conn_label.pack(side="left", padx=5)
        
        # Last RX
        self.status_rx_label = tk.Label(status_frame, text="RX: --", 
                                       bg="#2b2b2b", fg="#66ff66", 
                                       font=("Arial", 10),
                                       width=10, anchor="w")
        self.status_rx_label.pack(side="left", padx=5)
        
        # Last TX
        self.status_tx_label = tk.Label(status_frame, text="TX: --", 
                                       bg="#2b2b2b", fg="#6666ff", 
                                       font=("Arial", 10),
                                       width=10, anchor="w")
        self.status_tx_label.pack(side="left", padx=5)
        
        # RX Rate
        self.status_rx_rate = tk.Label(status_frame, text="↓ 0 msg/s", 
                                     bg="#2b2b2b", fg="#66ccff", 
                                     font=("Arial", 10),
                                     width=12, anchor="w")
        self.status_rx_rate.pack(side="left", padx=5)
        
        # TX Rate
        self.status_tx_rate = tk.Label(status_frame, text="↑ 0 msg/s", 
                                     bg="#2b2b2b", fg="#66ccff", 
                                     font=("Arial", 10),
                                     width=12, anchor="w")
        self.status_tx_rate.pack(side="left", padx=5)
        
        # Motor temp
        self.status_motor_temp = tk.Label(status_frame, text="🌡️ --°C", 
                                        bg="#2b2b2b", fg="#ff9966", 
                                        font=("Arial", 10),
                                        width=12, anchor="w")
        self.status_motor_temp.pack(side="left", padx=5)
        
        # Start status update timer
        self.schedule_status_update()

    def setup_matplotlib_graph(self, parent):
        """Setup matplotlib graph with dark theme and dual Y-axes"""
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        
        # Configure dark theme for matplotlib
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#1a1a1a')
        
        # Create secondary Y-axis for torque
        self.ax2 = self.ax.twinx()
        self.ax2.set_facecolor('#1a1a1a')
        
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.get_tk_widget().configure(bg='#2b2b2b')
        
        # Initialize plot lines - velocity and position on left axis
        self.velocity_line, = self.ax.plot([], [], '#4a9eff', linewidth=2, label='Velocity (RPM)')
        self.position_line, = self.ax.plot([], [], '#ff6b6b', linewidth=2, label='Position (°)')
        
        # Torque on right axis
        self.torque_line, = self.ax2.plot([], [], '#4ecdc4', linewidth=2, label='Torque (A)')
        
        # Configure left axis (velocity/position)
        self.ax.set_xlabel('Time (s)', color='#e0e0e0')
        self.ax.set_ylabel('Velocity (RPM) / Position (°)', color='#e0e0e0')
        self.ax.tick_params(axis='y', colors='#e0e0e0')
        self.ax.tick_params(axis='x', colors='#e0e0e0')
        
        # Configure right axis (torque)
        self.ax2.set_ylabel('Torque (A)', color='#4ecdc4')
        self.ax2.tick_params(axis='y', colors='#4ecdc4')
        
        # Grid and styling
        self.ax.grid(True, color='#4a4a4a', alpha=0.5)
        self.ax.spines['bottom'].set_color('#5a5a5a')
        self.ax.spines['top'].set_color('#5a5a5a')
        self.ax.spines['left'].set_color('#5a5a5a')
        self.ax2.spines['right'].set_color('#5a5a5a')
        
        # Combine legends from both axes in fixed position
        lines1, labels1 = self.ax.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        self.ax.legend(lines1 + lines2, labels1 + labels2, 
                      loc='upper left', facecolor='#3c3c3c', 
                      edgecolor='#5a5a5a', labelcolor='#e0e0e0')
        
        # Use Tkinter timer instead of matplotlib animation for better integration
        self.graph_start_time = time.time()
        self._start_graph_updates()
        print("✅ Graph updates started with Tkinter timer")
    
    def _start_graph_updates(self):
        """Start graph updates using Tkinter's after method"""
        self._update_graph_timer()
    
    def _update_graph_timer(self):
        """Timer-based graph update"""
        try:
            if hasattr(self, 'canvas') and self.canvas:
                self.update_graph(None)  # Call update_graph with dummy frame parameter
                self.canvas.draw()  # Force canvas redraw
        except Exception as e:
            print(f"Graph update error: {e}")
        
        # Schedule next update in 100ms - use try/except to handle timer cleanup
        try:
            if hasattr(self, 'root') and self.root:
                self.root.after(100, self._update_graph_timer)
        except tk.TclError:
            # Widget destroyed, stop timer
            pass
        
    def setup_text_graph(self, parent):
        """Setup text-based graph fallback"""
        self.graph_display = scrolledtext.ScrolledText(parent, height=15, width=60, font=("Courier", 9))
        self.graph_display.pack(fill="both", expand=True)
        
    def update_graph(self, frame):
        """Update matplotlib graph with dual Y-axes - robust version"""
        try:
            # Graph update function is being called by Tkinter timer
            # Verify we have data and attributes
            if not hasattr(self, 'plot_time') or not hasattr(self, 'ax') or not hasattr(self, 'ax2'):
                return []
            
            # Thread-safe access to plot data length
            try:
                data_length = len(self.plot_time) if hasattr(self, 'plot_time') and self.plot_time else 0
            except:
                data_length = 0
            
            # Graph update working
                
            if data_length == 0:
                # Clear all plot lines
                self.velocity_line.set_data([], [])
                self.position_line.set_data([], [])  
                self.torque_line.set_data([], [])
                
                # Clear axes
                self.ax.clear()
                self.ax2.clear()
                
                # Display "No data received" message in red
                self.ax.text(0.5, 0.5, 'No data received', 
                           transform=self.ax.transAxes, 
                           fontsize=16, color='red', 
                           ha='center', va='center',
                           weight='bold')
                
                # Restore axis styling for dark theme
                self.ax.set_facecolor('#1e1e1e')
                self.ax.tick_params(colors='#e0e0e0')
                self.ax.spines['bottom'].set_color('#5a5a5a')
                self.ax.spines['top'].set_color('#5a5a5a') 
                self.ax.spines['left'].set_color('#5a5a5a')
                self.ax.spines['right'].set_color('#5a5a5a')
                
                # Set minimal axis ranges to prevent auto-scaling issues
                self.ax.set_xlim(0, 1)
                self.ax.set_ylim(0, 1)
                
                return []
            
            # We have data - proceed to plot it
            # Plotting data
            
            # Clear axes first to remove "No data received" text, then re-setup
            self.ax.clear()
            self.ax2.clear()
            
            # Re-create plot lines after clearing
            self.velocity_line, = self.ax.plot([], [], '#4a9eff', linewidth=2, label='Velocity (RPM)')
            self.position_line, = self.ax.plot([], [], '#ff6b6b', linewidth=2, label='Position (°)')
            self.torque_line, = self.ax2.plot([], [], '#4ecdc4', linewidth=2, label='Torque (A)')
            
            # Re-setup axes styling
            self.ax.set_facecolor('#1e1e1e')
            self.ax2.set_facecolor('#1a1a1a')
            self.ax.tick_params(colors='#e0e0e0')
            self.ax2.tick_params(colors='#e0e0e0')
            self.ax.set_xlabel('Time (s)', color='#e0e0e0')
            self.ax.set_ylabel('Velocity/Position', color='#e0e0e0')
            self.ax2.set_ylabel('Torque (A)', color='#e0e0e0')
            self.ax.grid(True, color='#4a4a4a', alpha=0.5)
            
            # Ensure all data arrays have the same length as plot_time
            min_length = len(self.plot_time)
            if self.plot_velocity:
                min_length = min(min_length, len(self.plot_velocity))
            if self.plot_position:
                min_length = min(min_length, len(self.plot_position))
            if self.plot_torque:
                min_length = min(min_length, len(self.plot_torque))
            
            # If data is inconsistent, trim to smallest common length
            if min_length < len(self.plot_time):
                self.plot_time = deque(list(self.plot_time)[-min_length:], maxlen=self.max_plot_points)
                self.plot_velocity = deque(list(self.plot_velocity)[-min_length:], maxlen=self.max_plot_points)
                self.plot_position = deque(list(self.plot_position)[-min_length:], maxlen=self.max_plot_points)
                self.plot_torque = deque(list(self.plot_torque)[-min_length:], maxlen=self.max_plot_points)
            
            times = list(self.plot_time)
            if not times:
                return []
            
            lines = []
            # Left axis data (velocity and position)
            left_has_data = False
            
            try:
                if self.show_velocity_var.get() and len(self.plot_velocity) >= len(times):
                    velocity_data = list(self.plot_velocity)[:len(times)]
                    self.velocity_line.set_data(times, velocity_data)
                    lines.append(self.velocity_line)
                    left_has_data = True
                    # Velocity line updated successfully
            except Exception as e:
                print(f"Warning: Error updating velocity line: {e}")
                
            try:
                if self.show_position_var.get() and len(self.plot_position) >= len(times):
                    position_data = list(self.plot_position)[:len(times)]
                    self.position_line.set_data(times, position_data)
                    lines.append(self.position_line)
                    left_has_data = True
            except Exception as e:
                print(f"Warning: Error updating position line: {e}")
            
            # Right axis data (torque)
            right_has_data = False
            try:
                if self.show_torque_var.get() and len(self.plot_torque) >= len(times):
                    torque_data = list(self.plot_torque)[:len(times)]
                    self.torque_line.set_data(times, torque_data)
                    lines.append(self.torque_line)
                    right_has_data = True
            except Exception as e:
                print(f"Warning: Error updating torque line: {e}")
                
            # Update X-axis limits
            try:
                if times:
                    self.ax.set_xlim(max(0, times[0]), times[-1] + 1)
            except Exception as e:
                print(f"Warning: Error setting x-axis limits: {e}")
                
            # Update left axis scaling for velocity/position
            if left_has_data:
                try:
                    all_left_data = []
                    if self.show_velocity_var.get() and self.plot_velocity:
                        all_left_data.extend([v for v in self.plot_velocity if isinstance(v, (int, float)) and not math.isnan(v) and not math.isinf(v)])
                    if self.show_position_var.get() and self.plot_position:
                        all_left_data.extend([p for p in self.plot_position if isinstance(p, (int, float)) and not math.isnan(p) and not math.isinf(p)])
                    
                    if all_left_data:
                        y_min = min(all_left_data)
                        y_max = max(all_left_data)
                        margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
                        self.ax.set_ylim(y_min - margin, y_max + margin)
                except Exception as e:
                    print(f"Warning: Error scaling left axis: {e}")
                    # Set default limits if scaling fails
                    try:
                        self.ax.set_ylim(-200, 400)
                    except:
                        pass
            
            # Update right axis scaling for torque independently
            if right_has_data and self.plot_torque:
                try:
                    valid_torque = [t for t in self.plot_torque if isinstance(t, (int, float)) and not math.isnan(t) and not math.isinf(t)]
                    if valid_torque:
                        torque_min = min(valid_torque)
                        torque_max = max(valid_torque)
                        margin = (torque_max - torque_min) * 0.1 if torque_max != torque_min else 0.5
                        self.ax2.set_ylim(torque_min - margin, torque_max + margin)
                except Exception as e:
                    print(f"Warning: Error scaling right axis: {e}")
                    # Set default limits if scaling fails
                    try:
                        self.ax2.set_ylim(-10, 10)
                    except:
                        pass
                
            # Use draw_idle for better performance
            try:
                self.canvas.draw_idle()
            except Exception as e:
                print(f"Warning: Error drawing canvas: {e}")
                # Try to recover by recreating the canvas if needed
                pass
                
            return lines
            
        except Exception as e:
            print(f"Error in update_graph: {e}")
            # Return empty list to keep animation running
            return []

    def refresh_ports(self):
        """Refresh available serial ports with smart filtering"""
        all_ports = serial.tools.list_ports.comports()
        
        # Filter for likely USB-to-RS485 devices
        valid_ports = []
        for port in all_ports:
            # Remove /dev/ prefix from device name for cleaner display
            device_name = port.device.replace('/dev/', '')
            
            # Skip ports with no description or generic descriptions
            if not port.description or port.description.lower() in ['n/a', 'unknown', '']:
                # Only include ttyUSB* devices even without description
                if 'ttyUSB' in port.device or 'ttyACM' in port.device:
                    port_info = f"{device_name} - Serial Port"
                    valid_ports.append((port.device, port_info))
                continue
            
            # Check for common USB-to-RS485 identifiers in description
            usb_rs485_keywords = [
                'usb', 'ftdi', 'ch340', 'ch341', 'cp210', 'pl2303', 'ft232',
                'converter', 'adapter', 'bridge', 'uart', 'rs485', 'rs232'
            ]
            
            description_lower = port.description.lower()
            
            # Include if description contains USB-to-serial keywords
            if any(keyword in description_lower for keyword in usb_rs485_keywords):
                # Clean up redundant descriptions (e.g., "FT232R USB UART - FT232R USB UART")
                description_parts = port.description.split(' - ')
                if len(description_parts) > 1 and description_parts[0] == description_parts[1]:
                    clean_description = description_parts[0]
                else:
                    clean_description = port.description
                
                port_info = f"{device_name} - {clean_description}"
                valid_ports.append((port.device, port_info))
        
        # If no filtered ports, fall back to all ports
        if not valid_ports:
            valid_ports = [(port.device, f"{port.device.replace('/dev/', '')} - {port.description}") for port in all_ports]
        
        # Update combo box with descriptions
        port_values = [info for device, info in valid_ports]
        port_devices = [device for device, info in valid_ports]
        
        self.port_combo['values'] = port_values
        self._port_device_map = dict(zip(port_values, port_devices))
        
        # Auto-connect logic
        if len(valid_ports) == 1 and not self.port_var.get():
            # Only one valid port - auto-select and log
            self.port_var.set(port_values[0])
            self.log_message(f"🔌 Auto-selected: {port_values[0]}")
            
            # Auto-connect after a short delay
            self.schedule_callback(1000, self.auto_connect_single_port)
        elif valid_ports and not self.port_var.get():
            # Multiple ports - just select the first one
            self.port_var.set(port_values[0])
    
    def auto_connect_single_port(self):
        """Auto-connect when only one valid port is available"""
        if not self.motor_controller and len(self.port_combo['values']) == 1:
            self.log_message("🔄 Auto-connecting to single USB-to-RS485 device...")
            self.connect_motor()
            # Note: auto-detect will be called automatically after connection

    def connect_motor(self):
        """Connect to motor"""
        try:
            port_info = self.port_var.get()
            if not port_info:
                self.log_message("❌ No port selected")
                return
            
            # Get actual device path from the mapping
            if hasattr(self, '_port_device_map') and port_info in self._port_device_map:
                port_device = self._port_device_map[port_info]
            else:
                # Fallback: extract device from port_info or use directly
                port_device = port_info.split(' - ')[0] if ' - ' in port_info else port_info
                
            # Use command queue instead of direct motor controller
            self.motor_controller = MotorCommandQueue(port=port_device)
            
            # Setup callbacks
            self.motor_controller.on_feedback = self._on_motor_feedback
            self.motor_controller.on_error = self._on_motor_error
            self.motor_controller.on_command_sent = self._on_command_sent
            
            if self.motor_controller.connect():
                self.connection_status.config(text="Connected", foreground="green")
                self.log_message(f"✅ Connected to {port_device}")
                self.estop_button.config(state="normal")  # Enable E-stop button
                self.status_conn_label.config(text="⚡ CONNECTED", fg="#66ff66")
                
                # Command queue handles feedback monitoring automatically
                # No need for separate monitoring thread
                # Auto-detect motor after connection
                self.schedule_callback(100, self.auto_detect_motor)
            else:
                self.log_message(f"❌ Failed to connect to {port_device}")
                
        except Exception as e:
            self.log_message(f"❌ Connection error: {e}")
    
    def _on_motor_feedback(self, motor_id, feedback):
        """Handle feedback from command queue - called from background thread"""
        try:
            # Callback is working correctly
            # Validate feedback data
            if not feedback or not hasattr(feedback, 'velocity') or not hasattr(feedback, 'position') or not hasattr(feedback, 'torque'):
                return
            
            # Update plot data (thread-safe)
            current_time = time.time() - self.start_time if hasattr(self, 'start_time') else 0
            
            if not hasattr(self, 'start_time'):
                self.start_time = time.time()
                current_time = 0
            
            # Validate data values before appending
            if isinstance(feedback.velocity, (int, float)) and not math.isnan(feedback.velocity) and not math.isinf(feedback.velocity):
                velocity = feedback.velocity
            else:
                velocity = 0.0
                
            if isinstance(feedback.position, (int, float)) and not math.isnan(feedback.position) and not math.isinf(feedback.position):
                position = feedback.position
            else:
                position = 0.0
                
            if isinstance(feedback.torque, (int, float)) and not math.isnan(feedback.torque) and not math.isinf(feedback.torque):
                torque = feedback.torque
            else:
                torque = 0.0
            
            # Append validated data
            self.plot_time.append(current_time)
            self.plot_velocity.append(velocity)
            self.plot_torque.append(torque)
            self.plot_position.append(position)
            
            # Data is being populated correctly
            
            # Update metrics (thread-safe)
            self.last_rx_time = time.time()
            self.rx_count += 1
            
            # Schedule GUI updates on main thread
            if hasattr(self, 'root'):
                try:
                    self.schedule_callback(0, lambda: self._update_gui_from_feedback(feedback))
                except Exception as e:
                    # Ignore errors if root is being destroyed
                    pass
                    
        except Exception as e:
            print(f"Error in _on_motor_feedback: {e}")
            # Continue operation even if this feedback fails
    
    def _update_gui_from_feedback(self, feedback):
        """Update GUI elements from feedback - runs on main thread"""
        try:
            # Update current mode display from feedback with color coding
            if len(feedback.raw_data) > 1:
                mode_val = feedback.raw_data[1]
                mode_names = {1: "Current", 2: "Velocity", 3: "Position"}
                mode_colors = {1: "#3a9f6b", 2: "#3a5f9f", 3: "#9f3a3a"}  # Green, Blue, Red
                if mode_val in mode_names:
                    self.control_mode_var.set(mode_names[mode_val])
                    if hasattr(self, 'mode_display'):
                        self.mode_display.config(foreground=mode_colors[mode_val])
            
            # Update temperature display
            if hasattr(feedback, 'temperature') and feedback.temperature > 0:
                temp_color = "#ff6666" if feedback.temperature > 70 else "#ff9966" if feedback.temperature > 50 else "#66ccff"
                if hasattr(self, 'status_temperature'):
                    self.status_temperature.config(text=f"{feedback.temperature}°C", foreground=temp_color)
                if hasattr(self, 'status_motor_temp'):
                    self.status_motor_temp.config(text=f"🌡️ {feedback.temperature}°C", fg=temp_color)
            else:
                # No temperature data
                if hasattr(self, 'status_temperature'):
                    self.status_temperature.config(text="N/A", foreground="gray")
                if hasattr(self, 'status_motor_temp'):
                    self.status_motor_temp.config(text="🌡️ --°C", fg="#888888")
            
            # Update connection screen status display
            if hasattr(self, 'status_velocity'):
                self.status_velocity.config(text=f"{feedback.velocity:.1f} RPM")
            if hasattr(self, 'status_position'):
                self.status_position.config(text=f"{feedback.position:.1f}°")
            if hasattr(self, 'status_torque'):
                self.status_torque.config(text=f"{feedback.torque:.2f} A")
                
        except Exception as e:
            # Ignore GUI update errors during shutdown
            pass
    
    def _on_motor_error(self, error_msg):
        """Handle errors from command queue with robust exception handling"""
        try:
            print(f"⚠️ Motor error: {error_msg}")
            try:
                self.log_message(f"⚠️ Motor: {error_msg}")
            except Exception:
                pass  # Ignore GUI errors during error handling
        except Exception:
            pass  # Never let error handling itself crash
    
    def _on_command_sent(self):
        """Handle command sent notification from queue with robust exception handling"""
        try:
            self.last_tx_time = time.time()
        except Exception:
            pass  # Ignore time update errors

    def disconnect_motor(self):
        """Disconnect from motor"""
        self.stop_monitoring()
        if self.motor_controller:
            self.motor_controller.disconnect()
            self.motor_controller = None
        self.connection_status.config(text="Disconnected", foreground="red")
        self.estop_button.config(state="disabled")  # Disable E-stop button
        self.status_conn_label.config(text="⚡ DISCONNECTED", fg="#ff6666")
        self.log_message("🔌 Disconnected")

    def auto_detect_motor(self):
        """Auto-detect motor ID and initialize position slider"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            self.log_message("❌ Not connected")
            return
            
        self.log_message("🔍 Detecting motors...")
        found = self.motor_controller.scan_motors(1, 10)
        
        if found:
            motor_id = found[0]
            self.motor_id_var.set(motor_id)
            self.log_message(f"✅ Found motor at ID {motor_id}")
            
            # Initialize position slider to current motor position
            # Do this after a brief delay to ensure connection is stable
            self.schedule_callback(500, lambda: self._initialize_position_slider(motor_id))
        else:
            self.log_message("⚠️ No motors detected")
    
    def register_validation_commands(self):
        """Register validation commands for entry fields"""
        # Integer validation (for velocity)
        self.vcmd_int = (self.root.register(self.validate_integer), '%P')
        # Decimal validation with 1 decimal place (for position and current)
        self.vcmd_decimal = (self.root.register(self.validate_decimal), '%P')
    
    def validate_integer(self, value_if_allowed):
        """Validate integer input"""
        if value_if_allowed == '' or value_if_allowed == '-':
            return True
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False
    
    def validate_decimal(self, value_if_allowed):
        """Validate decimal input with maximum 1 decimal place"""
        if value_if_allowed == '' or value_if_allowed == '-' or value_if_allowed == '.':
            return True
        try:
            # Check if it's a valid float
            float(value_if_allowed)
            # Check decimal places
            if '.' in value_if_allowed:
                decimal_part = value_if_allowed.split('.')[1]
                if len(decimal_part) > 1:
                    return False
            return True
        except ValueError:
            return False
    
    def _initialize_position_slider(self, motor_id):
        """Initialize position slider to current motor position without triggering commands"""
        try:
            # Temporarily disable the position slider callback
            self._updating_position_from_feedback = True
            
            # Request current motor position
            self.motor_controller.request_feedback(motor_id)
            
            # Wait briefly for feedback, then get the last known position
            def set_initial_position():
                feedback = self.motor_controller.get_last_feedback(motor_id)
                if feedback:
                    # Set position slider without triggering command (rounded to 1 decimal)
                    self.position_var.set(round(feedback.position, 1))
                    self.log_message(f"📍 Position slider initialized to {feedback.position:.1f}°")
                else:
                    self.log_message("⚠️ Could not read initial position")
                
                # Re-enable position slider callback
                self._updating_position_from_feedback = False
            
            self.schedule_callback(200, set_initial_position)
            
        except Exception as e:
            self.log_message(f"⚠️ Position initialization error: {e}")
            self._updating_position_from_feedback = False
    
    def set_motor_id(self):
        """Set motor ID using the Motor ID widget value as new target ID"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            self.log_message("❌ Not connected")
            return
        
        # Get the new target ID from the spinbox
        target_id = self.motor_id_var.get()
        
        # We need to find what motor is currently connected by scanning
        self.log_message(f"🔍 Scanning for current motor to change ID to {target_id}...")
        
        # Scan for active motors to find the current one
        found_motors = []
        for test_id in range(1, 11):
            if test_id != target_id:  # Don't test the target ID
                try:
                    feedback = self.motor_controller.request_feedback(test_id)
                    if feedback:
                        found_motors.append(test_id)
                except:
                    continue
        
        if not found_motors:
            self.log_message("❌ No active motor found to change ID")
            return
        
        if len(found_motors) > 1:
            self.log_message(f"⚠️ Multiple motors found: {found_motors}. Please disconnect others first.")
            return
            
        current_id = found_motors[0]
        
        if current_id == target_id:
            self.log_message(f"⚠️ Motor is already set to ID {target_id}")
            return
            
        self.log_message(f"🆔 Setting motor ID from {current_id} to {target_id}...")
        
        if self.motor_controller.set_motor_id(current_id, target_id):
            self.log_message(f"✅ Motor ID changed from {current_id} to {target_id}")
            self.log_message(f"💡 Motor now responds to ID {target_id}")
        else:
            self.log_message("❌ Failed to set motor ID")
    
    def start_motor(self):
        """Start motor with comprehensive startup sequence"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            self.log_message("❌ Not connected")
            return
            
        motor_id = self.motor_id_var.get()
        self.log_message("🚀 Starting motor startup sequence...")
        
        try:
            # Use the exact same sequence as the working motor diagnostic script
            
            # Start with gentle velocity using command queue
            self.log_message("  🚀 Starting gentle movement (25 RPM)...")
            self.motor_controller.set_velocity(motor_id, 25)
            self.log_message("✅ Motor start command sent via queue!")
                
        except Exception as e:
            self.log_message(f"❌ Motor startup failed: {e}")

    def diagnose_motor(self):
        """Comprehensive motor diagnostics - non-blocking version"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            self.log_message("❌ Not connected for diagnosis")
            return
            
        motor_id = self.motor_id_var.get()
        self.log_message("🔍 Running motor diagnostics...")
        
        # Run diagnostics asynchronously to avoid blocking GUI
        self._run_diagnose_step_1(motor_id)
    
    def _run_diagnose_step_1(self, motor_id):
        """Step 1: Test communication"""
        try:
            self.log_message("  📡 Testing communication...")
            feedback = self.motor_controller.request_feedback(motor_id)
            if feedback:
                self.log_message(f"  ✅ Communication OK - Motor ID {motor_id} responding")
                self.log_message(f"     Current state: {feedback.velocity:.1f}RPM, {feedback.position:.1f}°, {feedback.torque:.2f}A")
                # Schedule next step
                self.schedule_callback(200, lambda: self._run_diagnose_step_2(motor_id))
            else:
                self.log_message(f"  ❌ No response from Motor ID {motor_id}")
                self.log_message("     Try Auto Detect to find the correct motor ID")
        except Exception as e:
            self.log_message(f"❌ Communication test failed: {e}")
    
    def _run_diagnose_step_2(self, motor_id):
        """Step 2: Test motor enable"""
        try:
            self.log_message("  🔌 Testing motor enable...")
            self.motor_controller.enable(motor_id)
            self.log_message("  ✅ Motor enable command sent")
            # Schedule next step
            self.schedule_callback(200, lambda: self._run_diagnose_step_3(motor_id))
        except Exception as e:
            self.log_message(f"❌ Motor enable failed: {e}")
    
    def _run_diagnose_step_3(self, motor_id):
        """Step 3: Test mode setting"""
        try:
            from ddsm115 import MotorMode
            self.log_message("  ⚙️ Testing velocity mode...")
            self.motor_controller.set_mode(motor_id, MotorMode.VELOCITY)
            self.log_message("  ✅ Velocity mode set")
            # Schedule next step
            self.schedule_callback(200, lambda: self._run_diagnose_step_4(motor_id))
        except Exception as e:
            self.log_message(f"❌ Failed to set velocity mode: {e}")
    
    def _run_diagnose_step_4(self, motor_id):
        """Step 4: Test movement"""
        try:
            self.log_message("  🔄 Testing small movement (5 RPM for 2 seconds)...")
            self.motor_controller.set_velocity(motor_id, 5)
            self.log_message("  ✅ Velocity command sent")
            # Schedule movement check
            self.schedule_callback(2000, lambda: self._run_diagnose_step_5(motor_id))
        except Exception as e:
            self.log_message(f"❌ Failed to send velocity command: {e}")
    
    def _run_diagnose_step_5(self, motor_id):
        """Step 5: Check movement and complete"""
        try:
            feedback = self.motor_controller.request_feedback(motor_id)
            if feedback:
                if abs(feedback.velocity) > 1:
                    self.log_message(f"  ✅ Motor is moving! Velocity: {feedback.velocity:.1f} RPM")
                else:
                    self.log_message("  ⚠️ Motor not moving despite commands")
                    self.log_message("     Possible issues:")
                    self.log_message("     - Mechanical load too high")
                    self.log_message("     - Power supply insufficient") 
                    self.log_message("     - Motor brake engaged")
                    self.log_message("     - Motor disabled/faulted")
            
            # Stop the test movement
            self.motor_controller.set_velocity(motor_id, 0)
            self.log_message("🔍 Diagnosis complete")
            
        except Exception as e:
            self.log_message(f"❌ Movement check failed: {e}")

    def emergency_stop(self):
        """Emergency stop motor"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            return
            
        motor_id = self.motor_id_var.get()
        self.motor_controller.stop(motor_id)
        self.log_message("🛑 EMERGENCY STOP")
    
    def emergency_stop_all(self):
        """Emergency stop ALL motors when E-stop button pressed"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            return
        
        self.log_message("🛑🛑🛑 EMERGENCY STOP ALL MOTORS 🛑🛑🛑")
        
        # Stop monitoring to prevent interference
        self.monitoring = False
        
        # Try to stop all possible motor IDs (1-10)
        for motor_id in range(1, 11):
            try:
                self.motor_controller.stop(motor_id)
            except:
                pass  # Ignore errors, just try to stop everything
        
        # Also try to stop the currently selected motor specifically
        try:
            current_id = self.motor_id_var.get()
            self.motor_controller.stop(current_id)
        except:
            pass
        
        self.log_message("✅ Emergency stop command sent to all motors")

    def _on_slider_press(self, slider_type):
        """Handle when user starts dragging a slider"""
        self._slider_dragging[slider_type] = True
    
    def _on_velocity_release(self):
        """Handle velocity slider release - send command via queue"""
        try:
            self._slider_dragging['velocity'] = False
        except Exception:
            pass  # Ignore slider state errors
        
        try:
            if not self.motor_controller or not self.motor_controller.is_connected:
                return
                
            motor_id = self.motor_id_var.get()
            velocity = int(self.velocity_var.get())
            
            # Send command directly - queue handles mode switching
            self.motor_controller.set_velocity(motor_id, velocity)
            self.control_mode_var.set("Velocity")
            # Update mode display color immediately
            if hasattr(self, 'mode_display'):
                self.mode_display.config(foreground="#3a5f9f")  # Blue for velocity
                
        except Exception as e:
            # Log error but don't crash the GUI
            print(f"Error in velocity slider release: {e}")
            try:
                self.log_message(f"⚠️ Velocity slider error: {e}")
            except Exception:
                pass  # Even log_message might fail during shutdown
    
    def _verify_and_send_velocity(self, motor_id, velocity):
        """Verify velocity mode switch completed, then send command"""
        # Just send the command - the command queue handles mode switching automatically
        self._send_velocity_command(motor_id, velocity)
    
    def _send_velocity_command(self, motor_id, velocity):
        """Send velocity command after mode switch"""
        self.motor_controller.set_velocity(motor_id, velocity)
    
    def set_velocity(self):
        """Set motor velocity"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            self.log_message("❌ Not connected")
            return
            
        motor_id = self.motor_id_var.get()
        velocity = self.velocity_var.get()
        self.motor_controller.set_velocity(motor_id, velocity)
        self.log_message(f"🏃 Set velocity: {velocity} RPM")

    def _on_position_release(self):
        """Handle position slider release - send command via queue"""
        try:
            self._slider_dragging['position'] = False
        except Exception:
            pass  # Ignore slider state errors
        
        try:
            # Skip if we're updating from feedback
            if getattr(self, '_updating_position_from_feedback', False):
                return
            
            if not self.motor_controller or not self.motor_controller.is_connected:
                return
                
            motor_id = self.motor_id_var.get()
            position = round(self.position_var.get(), 1)
            
            # Round the displayed value to 1 decimal place
            self.position_var.set(position)
            
            # Send command directly - queue handles velocity ramping and mode switching
            self.motor_controller.set_position(motor_id, position)
            self.control_mode_var.set("Position")
            # Update mode display color immediately
            if hasattr(self, 'mode_display'):
                self.mode_display.config(foreground="#9f3a3a")  # Red for position
                
        except Exception as e:
            # Log error but don't crash the GUI
            print(f"Error in position slider release: {e}")
            try:
                self.log_message(f"⚠️ Position slider error: {e}")
            except Exception:
                pass  # Even log_message might fail during shutdown
    
    def _ramp_down_for_position(self, motor_id, target_position):
        """Ramp down velocity before switching to position mode"""
        from ddsm115 import MotorMode
        
        # First ensure we're in velocity mode for ramping
        self.motor_controller.set_mode(motor_id, MotorMode.VELOCITY)
        
        # Start ramping down velocity
        self._ramp_velocity_down(motor_id, target_position, 0)
    
    def _ramp_velocity_down(self, motor_id, target_position, step):
        """Gradually reduce velocity to prepare for position mode"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            return
        
        # Get current velocity
        feedback = self.motor_controller.request_feedback(motor_id)
        if not feedback:
            return
        
        current_vel = feedback.velocity
        
        # If velocity is low enough, switch to position mode
        if abs(current_vel) < 10:
            self._switch_to_position_mode(motor_id, target_position)
            return
        
        # Calculate next velocity step (reduce by 20% each step, minimum 10 RPM reduction)
        vel_reduction = max(abs(current_vel) * 0.2, 10)
        if current_vel > 0:
            next_vel = max(0, current_vel - vel_reduction)
        else:
            next_vel = min(0, current_vel + vel_reduction)
        
        # Send velocity command
        self.motor_controller.set_velocity(motor_id, int(next_vel))
        
        # Schedule next ramp step in 100ms
        self.schedule_callback(100, lambda: self._ramp_velocity_down(motor_id, target_position, step + 1))
    
    def _switch_to_position_mode(self, motor_id, position):
        """Switch to position mode and send position command"""
        from ddsm115 import MotorMode
        if self.motor_controller.set_mode(motor_id, MotorMode.POSITION):
            self.control_mode_var.set("Position")
            # Wait longer for mode switch and verify before sending command
            self.schedule_callback(300, lambda: self._verify_and_send_position(motor_id, position))
        else:
            print("Failed to switch to position mode")
    
    def _verify_and_send_position(self, motor_id, position):
        """Verify position mode switch completed, then send command"""
        # Verify mode switch worked
        feedback = self.motor_controller.request_feedback(motor_id)
        if feedback and len(feedback.raw_data) > 1:
            actual_mode = feedback.raw_data[1]
            if actual_mode == 3:  # Position mode
                self._send_position_command(motor_id, position)
            else:
                # Mode switch didn't complete, try once more
                print(f"Position mode verification failed (got {actual_mode}), retrying...")
                self.motor_controller.set_mode(motor_id, MotorMode.POSITION)
                self.schedule_callback(300, lambda: self._send_position_command(motor_id, position))
        else:
            # No feedback, send command anyway (fallback)
            self._send_position_command(motor_id, position)
    
    def _send_position_command(self, motor_id, position):
        """Send position command after mode switch"""
        self.motor_controller.set_position(motor_id, position)
    
    def set_position(self):
        """Set motor position - ensures motor is stopped first"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            self.log_message("❌ Not connected")
            return
            
        motor_id = self.motor_id_var.get()
        position = self.position_var.get()
        
        if self.motor_controller.set_position(motor_id, position):
            self.log_message(f"📍 Set position: {position}°")
        else:
            self.log_message("❌ Position command failed")

    def _on_current_release(self):
        """Handle current slider release - send command via queue"""
        try:
            self._slider_dragging['current'] = False
        except Exception:
            pass  # Ignore slider state errors
        
        try:
            if not self.motor_controller or not self.motor_controller.is_connected:
                return
                
            motor_id = self.motor_id_var.get()
            current = round(self.current_var.get(), 1)
            
            # Round the displayed value to 1 decimal place
            self.current_var.set(current)
            
            # Send command directly - queue handles mode switching
            self.motor_controller.set_current(motor_id, current)
            self.control_mode_var.set("Current")
            # Update mode display color immediately
            if hasattr(self, 'mode_display'):
                self.mode_display.config(foreground="#3a9f6b")  # Green for current
                
        except Exception as e:
            # Log error but don't crash the GUI
            print(f"Error in current slider release: {e}")
            try:
                self.log_message(f"⚠️ Current slider error: {e}")
            except Exception:
                pass  # Even log_message might fail during shutdown
    
    def _verify_and_send_current(self, motor_id, current):
        """Verify current mode switch completed, then send command"""
        # Verify mode switch worked
        feedback = self.motor_controller.request_feedback(motor_id)
        if feedback and len(feedback.raw_data) > 1:
            actual_mode = feedback.raw_data[1]
            if actual_mode == 1:  # Current mode
                self._send_current_command(motor_id, current)
            else:
                # Mode switch didn't complete, try once more
                print(f"Current mode verification failed (got {actual_mode}), retrying...")
                self.motor_controller.set_mode(motor_id, MotorMode.CURRENT)
                self.schedule_callback(200, lambda: self._send_current_command(motor_id, current))
        else:
            # No feedback, send command anyway (fallback)
            self._send_current_command(motor_id, current)
    
    def _send_current_command(self, motor_id, current):
        """Send current command after mode switch"""
        self.motor_controller.set_current(motor_id, current)
    
    
    def set_current(self):
        """Set motor current"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            self.log_message("❌ Not connected")
            return
            
        motor_id = self.motor_id_var.get()
        current = self.current_var.get()
        self.motor_controller.set_current(motor_id, current)
        self.log_message(f"⚡ Set current: {current} A")

    def stop_motor(self):
        """Stop motor"""
        if not self.motor_controller or not self.motor_controller.is_connected:
            return
            
        motor_id = self.motor_id_var.get()
        self.motor_controller.set_velocity(motor_id, 0)
        self.log_message("⏹️ Motor stopped")

    def start_monitoring(self):
        """Start monitoring motor status with robust exception handling"""
        try:
            if self.monitoring:
                return
                
            self.monitoring = True
            try:
                self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
                self.monitor_thread.start()
            except Exception as e:
                print(f"Warning: Failed to start monitoring thread: {e}")
                try:
                    self.monitoring = False
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Start monitoring error: {e}")
            try:
                self.monitoring = False
            except Exception:
                pass

    def stop_monitoring(self):
        """Stop monitoring with robust exception handling"""
        try:
            self.monitoring = False
        except Exception:
            pass

    def monitor_loop(self):
        """Monitor motor status in background"""
        while self.monitoring and self.motor_controller and self.motor_controller.is_connected:
            try:
                motor_id = self.motor_id_var.get()
                feedback = self.motor_controller.request_feedback(motor_id)
                
                if feedback:
                    # Update status display
                    # Don't track immediate feedback callbacks - they're essential for RX
                    self.schedule_callback(0, lambda: self.update_status_display(feedback))
                    
                    # Note: Graph data is populated by _on_motor_feedback() callback
                    # from motor_command_queue - no need to duplicate here
                
                # No motor state application needed with release-based control
                    
                time.sleep(0.1)  # 100ms update rate
                
            except Exception as e:
                pass  # Suppress monitoring errors

    def update_status_display(self, feedback):
        """Update status display"""
        self.status_velocity.config(text=f"{feedback.velocity:.1f} RPM")
        self.status_position.config(text=f"{feedback.position:.1f}°")
        self.status_torque.config(text=f"{feedback.torque:.2f} A")
        
        
        # Update temperature display
        if feedback.temperature > 0:
            temp_color = "red" if feedback.temperature > 70 else "orange" if feedback.temperature > 50 else "blue"
            self.status_temperature.config(text=f"{feedback.temperature}°C", foreground=temp_color)
        else:
            self.status_temperature.config(text="N/A", foreground="gray")

    def clear_graph(self):
        """Clear graph data"""
        self.plot_time.clear()
        self.plot_velocity.clear()
        self.plot_position.clear()
        self.plot_torque.clear()
        
        if not MATPLOTLIB_AVAILABLE and hasattr(self, 'graph_display'):
            self.graph_display.delete(1.0, tk.END)

    def clear_log(self):
        """Clear connection log"""
        self.connection_log.delete(1.0, tk.END)

    def log_message(self, message):
        """Log message with timestamp"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        self.connection_log.insert(tk.END, full_message)
        self.connection_log.see(tk.END)
        
        # Auto-cleanup: Keep only last 100 lines
        lines = self.connection_log.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.connection_log.delete(1.0, tk.END)
            self.connection_log.insert(1.0, '\n'.join(lines[-100:]))

    def _handle_sigint(self, signum, frame):
        """Handle Ctrl+C for immediate shutdown with robust exception handling"""
        try:
            if getattr(self, '_shutdown_in_progress', False):
                # Force exit if already shutting down
                try:
                    sys.exit(1)
                except Exception:
                    import os
                    os._exit(1)
        except Exception:
            pass
        
        try:
            self._shutdown_in_progress = True
        except Exception:
            pass
            
        try:
            print("\n⚡ Ctrl+C detected - Emergency shutdown...")
        except Exception:
            pass
        
        # Stop any motors immediately
        try:
            if hasattr(self, 'motor_controller') and self.motor_controller and self.motor_controller.is_connected:
                try:
                    # Emergency stop all motors
                    for motor_id in range(1, 11):
                        try:
                            self.motor_controller.emergency_stop(motor_id)
                        except Exception:
                            pass  # Ignore individual motor stop errors
                except Exception:
                    pass  # Ignore motor controller errors
        except Exception:
            pass
        
        # Schedule GUI shutdown on main thread without tracking (emergency case)
        try:
            if hasattr(self, 'root'):
                self.root.after(0, self._emergency_shutdown)
        except Exception:
            # If GUI is not responsive, force exit
            try:
                sys.exit(0)
            except Exception:
                import os
                os._exit(0)
    
    def _emergency_shutdown(self):
        """Emergency shutdown called from signal handler with robust exception handling"""
        try:
            # Set shutdown flag first to prevent new callbacks
            self._shutdown_in_progress = True
        except Exception:
            pass
            
        try:
            self.status_update_active = False
        except Exception:
            pass
        
        # Cancel all scheduled callbacks to prevent "invalid command name" errors
        try:
            self.cancel_all_callbacks()
        except Exception:
            pass
        
        # Stop monitoring immediately
        self.monitoring = False
        
        # Stop animation
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'ani'):
            try:
                self.ani.event_source.stop()
            except:
                pass
        
        # Disconnect motor controller quickly
        if self.motor_controller:
            try:
                self.motor_controller.disconnect()
            except:
                pass
        
        # Force quit immediately
        try:
            self.root.quit()
        except:
            pass
        
        try:
            self.root.destroy()
        except:
            pass
        
        # Force exit process immediately
        import os
        os._exit(0)
    
    def update_status_bar(self):
        """Update status bar metrics"""
        if not self.status_update_active or self._shutdown_in_progress:
            return
            
        current_time = time.time()
        
        # Calculate message rates every second
        if current_time - self.last_rate_calc >= 1.0:
            # Get stats from command queue if available
            if self.motor_controller and hasattr(self.motor_controller, 'get_stats'):
                stats = self.motor_controller.get_stats()
                
                # Calculate rates based on queue statistics
                commands_processed_delta = stats['commands_processed'] - getattr(self, '_last_commands_processed', 0)
                feedback_delta = stats['feedback_count'] - getattr(self, '_last_feedback_count', 0)
                
                self.tx_rate = commands_processed_delta
                self.rx_rate = feedback_delta
                
                # Store for next calculation
                self._last_commands_processed = stats['commands_processed']
                self._last_feedback_count = stats['feedback_count']
            else:
                # Fallback to old method
                self.rx_rate = self.rx_count
                self.tx_rate = self.tx_count
                self.rx_count = 0
                self.tx_count = 0
            
            self.last_rate_calc = current_time
            
            # Update rate displays
            self.status_rx_rate.config(text=f"↓ {self.rx_rate} msg/s")
            self.status_tx_rate.config(text=f"↑ {self.tx_rate} msg/s")
        
        # Update last message times
        if self.last_rx_time > 0:
            rx_age = current_time - self.last_rx_time
            if rx_age < 1:
                self.status_rx_label.config(text=f"RX: {rx_age*1000:.0f}ms", fg="#66ff66")
            else:
                self.status_rx_label.config(text=f"RX: {rx_age:.1f}s", fg="#ffff66")
        
        if self.last_tx_time > 0:
            tx_age = current_time - self.last_tx_time
            if tx_age < 1:
                self.status_tx_label.config(text=f"TX: {tx_age*1000:.0f}ms", fg="#6666ff")
            else:
                self.status_tx_label.config(text=f"TX: {tx_age:.1f}s", fg="#9999ff")
        
        # Schedule next update
        self.schedule_status_update()
    
    def schedule_status_update(self):
        """Schedule the next status update"""
        if (hasattr(self, 'root') and self.root and self.status_update_active and 
            not self._shutdown_in_progress):
            try:
                self.schedule_callback(100, self.update_status_bar)
            except tk.TclError:
                pass
    
    def on_motor_feedback(self, motor_id, feedback):
        """Handle motor feedback for metrics"""
        self.rx_count += 1
        self.last_rx_time = time.time()
        
        # Update temperature in status bar
        if feedback.temperature > 0:
            temp_color = "#ff6666" if feedback.temperature > 70 else "#ff9966" if feedback.temperature > 50 else "#66ccff"
            self.status_motor_temp.config(text=f"🌡️ {feedback.temperature}°C", fg=temp_color)
    
    def on_closing(self):
        """Handle window closing"""
        if self._shutdown_in_progress:
            return
        
        self._shutdown_in_progress = True
        self.status_update_active = False
        
        # Cancel all scheduled callbacks to prevent warnings
        try:
            for callback_id in list(self._scheduled_callbacks):
                try:
                    self.root.after_cancel(callback_id)
                except Exception:
                    pass
            self._scheduled_callbacks.clear()
        except Exception:
            pass
        
        self.stop_monitoring()
        
        # Stop matplotlib animation if it exists
        try:
            if MATPLOTLIB_AVAILABLE and hasattr(self, 'ani') and self.ani is not None:
                try:
                    # Properly stop and clean up animation
                    self.ani.event_source.stop()
                    self.ani.event_source = None
                    # Save the animation to prevent the "deleted without rendering" warning
                    if hasattr(self.ani, '_func'):
                        self.ani._func = None
                    self.ani = None
                except Exception as e:
                    print(f"Warning: Error stopping animation: {e}")
        except Exception as e:
            print(f"Warning: Error in animation cleanup: {e}")
        
        # Disconnect motor controller
        try:
            if hasattr(self, 'motor_controller') and self.motor_controller:
                try:
                    self.motor_controller.disconnect()
                except Exception as e:
                    print(f"Warning: Error disconnecting motor controller: {e}")
                finally:
                    try:
                        self.motor_controller = None
                    except Exception:
                        pass
        except Exception as e:
            print(f"Warning: Error accessing motor controller during shutdown: {e}")
        
        # Quit and destroy the GUI
        try:
            self.root.quit()  # Use quit() instead of destroy() for cleaner exit
        except Exception as e:
            print(f"Warning: Error quitting GUI: {e}")
            
        try:
            self.root.destroy()
        except Exception as e:
            print(f"Warning: Error destroying GUI: {e}")

def main():
    root = tk.Tk()
    app = SimpleDDSM115GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()